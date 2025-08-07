import pytest

from gh_tt.classes.gitter import Gitter
from gh_tt.classes.semver import ExecutionMode, ReleaseType, Semver


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

    assert "1.0.1-rc\n" in output
    assert "1.0.11rc\n" in output

    semver.list(release_type=ReleaseType.RELEASE)
    output = capsys.readouterr().out
    assert "0.7.3\n" in output
    assert "0.6.1\n" in output

    release = semver.get_current_semver()
    assert release == "0.7.3"

    prerelease = semver.get_current_semver(release_type=ReleaseType.PRERELEASE)
    assert prerelease == "1.0.11rc"

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
