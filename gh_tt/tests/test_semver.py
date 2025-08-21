from enum import Enum, auto
import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gh_tt.classes.gitter import Gitter
from gh_tt.classes.semver import ExecutionMode, ReleaseType, Semver, SemverTag, SemverVersion
from gh_tt.tests.testbed import Testbed


@pytest.mark.unittest
def test_semver_init(capsys):
    Gitter.verbose = False

    semver = Semver()
    assert isinstance(semver, Semver)
    assert semver.get("initial") == "0.0.0"
    semver = None

    semver = Semver(suffix="pending", prefix="v", initial="1.4.1")
    assert isinstance(semver, Semver)
    assert semver.get("initial") == "1.4.1"
    assert semver.get("suffix") == "pending"
    assert semver.get("prefix") == "v"

    semver = None

    with pytest.raises(SystemExit) as cm:
        semver = Semver(initial="bad.initial.3")

    assert cm.value.code == 1
    assert "Invalid initial version" in capsys.readouterr().err


@pytest.mark.unittest
def test_semver_list(capsys):
    # Setup
    semver = Semver().from_json("gh_tt/tests/data/semver/semver_loaded_release_and_prerelease.json")
    assert isinstance(semver, Semver)

    semver.list(release_type=ReleaseType.PRERELEASE)
    output = capsys.readouterr().out

    assert "1.0.1-rc1\n" in output
    assert "1.0.11-rc1\n" in output

    semver.list(release_type=ReleaseType.RELEASE)
    output = capsys.readouterr().out
    assert "0.7.3\n" in output
    assert "0.6.1\n" in output

@pytest.mark.unittest
def test_semver_get_current():
    semver = Semver().from_json('gh_tt/tests/data/semver/semver_loaded_release_and_prerelease.json')

    release = semver.get_current_semver()
    assert str(release) == "0.7.3"

    prerelease = semver.get_current_semver(release_type=ReleaseType.PRERELEASE)
    assert str(prerelease) == "1.0.11-rc1"

@pytest.mark.unittest
def test_semver_bump(capsys):
    semver = Semver().from_json('gh_tt/tests/data/semver/semver_loaded_release_and_prerelease.json')

    semver.bump("patch", message="Test patch bump", release_type=ReleaseType.PRERELEASE, execution_mode=ExecutionMode.DRY_RUN)
    assert "git tag -a -m \"1.0.12rc\nBumped patch from version '1.0.11rc' to '1.0.12rc'\nTest patch bump\" 1.0.12rc\n" in capsys.readouterr().out


@pytest.mark.unittest
def test_semver_first_prerelease(capsys):
    # Setup
    semver = Semver().from_json("gh_tt/tests/data/semver/semver_loaded_release.json")
    assert isinstance(semver, Semver)

    semver.list(release_type=ReleaseType.PRERELEASE)
    assert capsys.readouterr().out == ""

    semver.list(release_type=ReleaseType.RELEASE)
    output = capsys.readouterr().out
    assert "0.7.3\n" in output
    assert "0.6.1\n" in output

    release = semver.get_current_semver()
    assert release == "0.7.3"

    prerelease = semver.get_current_semver(release_type=ReleaseType.PRERELEASE)
    assert prerelease is None

    semver.bump("patch", message="Test patch bump", release_type=ReleaseType.PRERELEASE, execution_mode=ExecutionMode.DRY_RUN)
    assert "git tag -a -m \"0.0.1rc\nBumped patch from version 'None' to '0.0.1rc'\nTest patch bump\" 0.0.1rc\n" in capsys.readouterr().out

@pytest.mark.integration
def test_note_with_one_release():
    [extension_list, _] = Testbed.gitter_run(cmd='gh extension list')
    if 'thetechcollective/gh-tt' in extension_list:
        raise SystemExit(
            "You have a remote version of the 'gh-tt' extension installed.\n"
            "Your local changes would not be taken into consideration when running the integration test.\n"
            "Remove the existing extension with `gh extension remove gh-tt`, then \n"
            "install the local version with `gh extension install .`"
        )

    with Testbed.create_local_repo() as repo:
        (repo / 'file1.txt').write_text('text')
        Testbed.gitter_run_all(['git add .', 'git commit -m "file1"'], cwd=repo)
        (repo / 'file2.txt').write_text('text')
        Testbed.gitter_run_all(['git add .', 'git commit -m "file2"', 'git tag 1.0.0', 'gh tt semver note --filename note.md'], cwd=repo)

        assert (repo / 'note.md').read_text().find('Release Notes') != -1

@st.composite
def semver_versions(draw, *, with_prerelease: bool = False, prerelease_id: str | None = None) -> SemverVersion:
    # If prerelease_id is provided, use it; otherwise generate random one
    identifier = None
    if with_prerelease:
        if prerelease_id is not None:
            identifier = prerelease_id
        else:
            identifier = draw(st.text(alphabet=list(string.ascii_lowercase), min_size=1, max_size=15))
    
    return SemverVersion(
        major=draw(st.integers(min_value=0)),
        minor=draw(st.integers(min_value=0)),
        patch=draw(st.integers(min_value=0)),
        prerelease_identifier=identifier,
        prerelease=draw(st.integers(min_value=1)) if with_prerelease else None,
    )

class PrereleaseStrategy(Enum):
    MIXED = auto()
    CONSISTENT = auto()
    

@st.composite
def tag_strings(draw, *, prerelease_strategy: PrereleaseStrategy = PrereleaseStrategy.MIXED) -> str:
    if prerelease_strategy is PrereleaseStrategy.CONSISTENT:
        # Generate a shared prerelease identifier for all prereleases
        shared_id = draw(st.text(alphabet=list(string.ascii_lowercase), min_size=1, max_size=15))
        valid_versions = draw(
            st.lists(
                st.one_of(
                    semver_versions(with_prerelease=False),
                    semver_versions(with_prerelease=True, prerelease_id=shared_id),
                )
            )
        )
    else:  # Prerelease identifier is randomly generated for each SemverVersion
        valid_versions = draw(st.lists(semver_versions(with_prerelease=draw(st.booleans()))))

    other_tags = draw(
        st.lists(
            st.text(alphabet=list(string.ascii_lowercase), min_size=1, max_size=15).filter(
                lambda x: "\n" not in x
            ),
        )
    )

    valid_version_strings = [str(version) for version in valid_versions]
    all_tags = valid_version_strings + other_tags

    draw(st.randoms()).shuffle(all_tags)
    return "\n".join(all_tags)

@pytest.mark.pbt
@given(version=semver_versions())
def test_semver_version_bump(version):

    # Major bump resets minor and patch
    version_major_bumped = version.bump_major()
    assert version_major_bumped.major == version.major + 1
    assert version_major_bumped.minor == 0
    assert version_major_bumped.patch == 0

    # Minor bump resets patch
    version_minor_bumped = version.bump_minor()
    assert version_minor_bumped.major == version.major
    assert version_minor_bumped.minor == version.minor + 1
    assert version_minor_bumped.patch == 0

    # Patch bump increments patch
    version_patch_bumped = version.bump_patch()
    assert version_patch_bumped.major == version.major
    assert version_patch_bumped.minor == version.minor
    assert version_patch_bumped.patch == version.patch + 1


@pytest.mark.pbt
@given(version=semver_versions(with_prerelease=True))
def test_semver_prerelease_bump(version):

    # Prerelease bump increments prerelease
    version_prerelease_bumped = version.bump_prerelease()
    assert version_prerelease_bumped.major == version.major
    assert version_prerelease_bumped.minor == version.minor
    assert version_prerelease_bumped.patch == version.patch
    assert version_prerelease_bumped.prerelease_identifier == version.prerelease_identifier
    assert version_prerelease_bumped.prerelease == version.prerelease + 1

    # Major/minor/patch bump resets prerelease
    version_major_bumped = version.bump_major()
    assert version_major_bumped.prerelease is None
    assert version_major_bumped.prerelease_identifier is None

    # Minor bump resets patch
    version_minor_bumped = version.bump_minor()
    assert version_minor_bumped.prerelease is None
    assert version_minor_bumped.prerelease_identifier is None

    # Patch bump increments patch
    version_patch_bumped = version.bump_patch()
    assert version_patch_bumped.prerelease is None
    assert version_patch_bumped.prerelease_identifier is None

@pytest.mark.pbt
@given(version=semver_versions())
def test_semver_parse_roundtrip(version):
    version_str = str(version)
    assert version == SemverVersion.from_string(version_str)

@pytest.mark.unittest
@pytest.mark.parametrize('invalid_version', [
    '01.0.0', # leading zero
    '0.1.', # missing digit
    '0.01', # missing dot
    '0.0.0rc1', # missing hyphen in front of prerelease identifier
    '0.0.0-rc', # missing digit after prerelease identifier
    '0.0.0-rc0', # zero after prerelease identifier
    '0.0.0+rc1', # plus instead of hyphen before prerelease identifier
])
def test_parsing_raises_on_invalid_semver(invalid_version):
    with pytest.raises(ValueError, match='Invalid semver format:'):
        SemverVersion.from_string(invalid_version)

@pytest.mark.pbt
@given(tag_string=tag_strings().filter(lambda x: x.strip() != ''))
def test_parse_tags(tag_string: str):
    new_lines = len(tag_string.split('\n'))

    parsed = Semver()._parse_tags(tag_string=tag_string, prefix = None)

    # No tags disappear when parsing
    assert len(parsed['release']) + len(parsed['prerelease']) + len(parsed['other']) == new_lines
