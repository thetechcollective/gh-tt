from __future__ import annotations

import asyncio
import re
import sys
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.lazyload import Lazyload


class ReleaseType(StrEnum):
    RELEASE = 'release'
    PRERELEASE = 'prerelease'

class ExecutionMode(Enum):
    LIVE = auto()
    DRY_RUN = auto()

@dataclass(order=True, frozen=True)
class SemverVersion:
    major: int
    minor: int
    patch: int
    prerelease: int | None = None
    prerelease_identifier: str | None = None

    def __post_init__(self):
        pass

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease_identifier}{self.prerelease}"

        return version
    
    def bump_major(self) -> SemverVersion:
        return SemverVersion(self.major + 1, 0, 0, None, None)
    
    def bump_minor(self) -> SemverVersion:
        return SemverVersion(self.major, self.minor + 1, 0, None, None)
    
    def bump_patch(self) -> SemverVersion:
        return SemverVersion(self.major, self.minor, self.patch + 1, None, None)
    
    def bump_prerelease(self, prefix: str | None) -> SemverVersion:
        if prefix is None:
            prefix = ''
        
        prerelease = self.prerelease + 1 if self.prerelease is not None else 1

        return SemverVersion(self.major, self.minor, self.patch, prerelease, prefix)
    
    def is_prerelease(self):
        return self.prerelease is not None
    
    @classmethod
    def from_string(cls, version_str: str) -> SemverVersion:
        pattern = r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease_identifier>[a-z]+)(?P<prerelease>[1-9]\d*))?$'
        match = re.match(pattern, version_str)
        
        if not match:
            raise ValueError(f"Invalid semver format: {version_str}")
        
        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=int(match.group('prerelease')) if match.group('prerelease') is not None else None,
            prerelease_identifier=match.group('prerelease_identifier')
        )
    
@dataclass(frozen=True)
class SemverTag:
    version: SemverVersion
    prefix: str | None = None

    def __str__(self) -> str:
        prefix_str = self.prefix if self.prefix is not None else ''
        return f'{prefix_str}{self.version}'
    
    def __lt__(self, other) -> bool:
        assert isinstance(other, SemverTag)
        
        return self.version < other.version
    
    @classmethod
    def from_string(cls, tag: str, prefix: str | None) -> SemverTag | None:
        version_str = tag
        if prefix is not None and prefix:
            version_str = tag.split(prefix)[1]

        try:
            version = SemverVersion.from_string(version_str)
        except ValueError:
            return None

        return cls(version, prefix)

class Semver(Lazyload):
    """Class used to represent the semver state of git repository"""

    def __init__(self, suffix: str | None = None, prefix: str | None = None, initial: str | None = None, tag_string: str | None = None):
        super().__init__()

        if initial is not None and initial != '':
            try:
                assert re.match(r'^\d+\.\d+\.\d+$', initial), "Initial version must be in the format 'X.Y.Z' where X, Y, Z are integers."
            except AssertionError as e:
                print(f"Invalid initial version format: {e}", file=sys.stderr)
                sys.exit(1)
            self.set('initial', initial)
        else:
            self.set('initial', Config.config()['semver']['initial'])

        if suffix is not None and suffix != '':
            self.set('suffix', suffix)
        else:
            self.set('suffix', Config.config()['semver']['prerelease_suffix'])

        if prefix is not None and prefix != '':
            self.set('prefix', prefix)
        else:
            self.set('prefix', Config.config()['semver']['prefix'])

        if tag_string is not None:
            self.set('tags', tag_string)
            self.set('semver_tags', self._parse_tags(tag_string, prefix))

    @classmethod
    def with_tags_loaded(cls) -> Semver:
        semver = cls()
        asyncio.run(semver._assert_props(['tags']))
        semver.set('semver_tags', semver._parse_tags(semver.get('tags'), semver.get('prefix')))

        return semver
    
    def _parse_tags(self, tag_string: str, prefix: str | None) -> dict:
        tags = tag_string.split('\n') if tag_string else []

        semver_tags = {
            'current': {
                'release': [],
                'prerelease': [],
                'other': [],
            }
        }

        for tag_str in tags:
            if not tag_str.strip(): # skip empty
                continue

            semver_tag = SemverTag.from_string(tag_str, prefix)
            if semver_tag:
                category = 'prerelease' if semver_tag.version.is_prerelease() else 'release'
                semver_tags['current'][category].append(semver_tag)
            else:
                semver_tags['current']['other'].append(tag_str)

        assert isinstance(semver_tags, dict)
        assert isinstance(semver_tags.get('current'), dict)
        assert all(isinstance(semver_tags['current'][category], list) for category in semver_tags['current'])
        assert all(category for category in semver_tags['current'] if category in ['release', 'prerelease', 'other'])

        return semver_tags
    

    def _get_next_semvers(self, current_release: SemverVersion | None, current_prerelease: SemverVersion | None, prerelease_identifier: str | None) -> dict:
        result = {
            'next_release_major': current_release.bump_major() if current_release is not None else None,
            'next_release_minor': current_release.bump_minor() if current_release is not None else None,
            'next_release_patch': current_release.bump_patch() if current_release is not None else None,
            'next_prerelease_major': current_prerelease.bump_major().bump_prerelease(prerelease_identifier) if current_prerelease is not None else current_release.bump_major().bump_prerelease(prerelease_identifier),
            'next_prerelease_minor': current_prerelease.bump_minor().bump_prerelease(prerelease_identifier) if current_prerelease is not None else current_release.bump_minor().bump_prerelease(prerelease_identifier),
            'next_prerelease_patch': current_prerelease.bump_patch().bump_prerelease(prerelease_identifier) if current_prerelease is not None else current_release.bump_patch().bump_prerelease(prerelease_identifier),
        }

        assert all(
            result[f'next_{release_type}_{level}'] 
            for release_type in ['release', 'prerelease']
            for level in ['major', 'minor', 'patch']
            if result[f'next_{release_type}_{level}'] is None or isinstance(result[f'next_{release_type}_{level}'], SemverVersion)
        )

        for k, v in result.items():
            self.set(k, v)

        return result
    

    def get_current_semver(self, release_type: ReleaseType = ReleaseType.RELEASE) -> SemverTag | None:
        """Returns the current semver tag"""
        current_tags = self.get('semver_tags')['current']

        if release_type is ReleaseType.RELEASE:
            return max(current_tags['release'], default=None)
        
        return max(current_tags['prerelease'], default=None)

    def bump(
            self, 
            level: str, 
            message: str | None,
            suffix: str | None = None,
            prefix: str | None = None,
            initial: str | None = None,
            release_type: ReleaseType = ReleaseType.RELEASE,
            execution_mode: ExecutionMode = ExecutionMode.LIVE
        ):

        assert level in ['major', 'minor', 'patch']

        if initial is not None:
            if not re.match(r'^\d+\.\d+\.\d+$', initial):
                print(f"⛔️ ERROR: Invalid initial version format '{initial}'. Must be in the format 'X.Y.Z' where X, Y, Z are integers.", file=sys.stderr)
                sys.exit(1)
        else:
            initial = self.get('initial')

        if prefix is None:
            prefix = self.get('prefix')

        if suffix is not None and suffix.strip() == '':
            print('⛔️ ERROR: Suffix must not contain only whitespace', file=sys.stderr)
            sys.exit(1)

        prerelease_identifier = suffix
        if prerelease_identifier is None:
            prerelease_identifier = self.get('suffix')

        message = f"\n{message}" if message else ""

        current_version = self.get_current_semver().version if self.get_current_semver() is not None else None
        current_prerelease_version = self.get_current_semver(ReleaseType.PRERELEASE).version if self.get_current_semver(ReleaseType.PRERELEASE) is not None else None

        self._get_next_semvers(current_version, current_prerelease_version, prerelease_identifier=prerelease_identifier)
        key = f'next_{release_type}_{level}'
        next_tag = f'{prefix}{self.get(key)}'


        from_version = self.get_current_semver(release_type)
        if from_version is None and release_type is ReleaseType.PRERELEASE:
            from_version = self.get_current_semver()

        cmd = f"git tag -a -m \"{next_tag}\nBumped {level} from version '{from_version}' to '{next_tag}'{message}\" {next_tag}"

        assert prefix is None or (prefix is not None and prefix in next_tag)
        assert release_type is ReleaseType.RELEASE or (
            (suffix is not None and suffix in next_tag) or (suffix is None)
        )

        if execution_mode is ExecutionMode.DRY_RUN:
            print(f"{cmd}")
            return cmd
        
        assert execution_mode is ExecutionMode.LIVE
        asyncio.run(Gitter(
            cmd=cmd,
            msg=f"Bumping {level} from version '{self.get_current_semver(release_type)}' to '{next_tag}'"
        ).run())

        return {next_tag}
    

    
    def list(self, release_type: ReleaseType = ReleaseType.RELEASE):
        """Lists the semver tags in the repository to stdout sorted by major, minor, patch."""

        current_tags = self.get('semver_tags')['current']
        category = 'prerelease' if release_type is ReleaseType.PRERELEASE else 'release'
        tags = sorted(current_tags[category])

        for tag in tags:
            print(tag)
            
    def note(self, release_type: ReleaseType = ReleaseType.RELEASE, filename: str | None = None) -> str:
        """Generates a release note either for a release or a prerelease, based on the set of current semver tags.

        Args:
            release_type (enum): If PRERELEASE, it will generate a note based on (current_release..current_prerelease). 
                               If RELEASE it will generate a note based on (previous_release..current_release)
                               Defaults to RELEASE.
            filename (str): If provided, the note will be written to this file. If None, it will be printed to stdout.
        
        Returns:
            str: The markdown note of changes between the two references.

        Raises:
            SystemExit(1): If the logical references are not valid tags in the git repo

        """

        if release_type is ReleaseType.PRERELEASE:
           from_ref = self.get_current_semver()
           to_ref = self.get_current_semver(release_type=ReleaseType.PRERELEASE)
        else:
            releases = sorted(self.get('semver_tags')['current']['release'])

            from_ref = None
            if len(releases) > 1:
                from_ref = self.get('semver_tags')['release'][releases[-2]]
            else:
                print("Could not find previous release tag when assembling changes for the note. Attempting to find a root commit instead.")
                [from_ref, _] = asyncio.run(Gitter(
                    cmd='git rev-list --max-parents=0 HEAD',
                    msg='Find root commits'
                ).run())

                if from_ref.find('\n') != -1:
                    print("Found multiple root commits. To create a note without any previous releases and multiple root commits, please create an explicit initial tag (e.g. 0.0.0). All changes from this ref will be included in the release note.", file=sys.stderr)
                    sys.exit(1)

                print("Found root commit. The release note will include all changes since the root commit, excluding the root commit.")
                  
            to_ref = self.get_current_semver()

        note = self.note_md(from_ref=from_ref, to_ref=to_ref)

        if filename is not None:
            # make sure the directory exists
            directory = Path(filename).parent
            if not Path.exists(directory):
                Path.mkdir(directory, parents=True)
            with Path.open(filename, 'w') as f:
                f.write(note)
        else:
            print(note)
        return note
    

    
    def note_md(self, from_ref:str, to_ref:str) -> str:
        """Generates a markdown note of changes between (from_ref..to_ref).
        The note is desinged to be saved to a file and attached to a GitHub release note (gh relsease create --notes-file ...).
        It will include a link to the changes between the two references, and a list of commits with their dates, commit messages, sha and authors.

        Args:
            from_ref (str): The reference to start from, defaults to the current semver tag.
            to_ref (str): The reference to end at, defaults to the next semver tag.

        Returns:
            str: The markdown note.

        Raises:
            SystemExit(1): If from_ref or to_ref are not valid tags in the git repo.
        """

        assert from_ref is not None, "from_ref must be provided"
        assert to_ref is not None, "to_ref must be provided"

        note = f"""## Release Notes for {to_ref}\n
This release includes the following [changes since {from_ref}](../../compare/{from_ref}..{to_ref}):\n"""

        cmd=f"git log --format='%n- **%cd**: %s%n%h %an' --date=format:'%Y-%m-%d' {from_ref}..{to_ref}"
        msg=f"Generating release notes from {from_ref} to {to_ref}" 

        [value, _] = asyncio.run(
            Gitter(
                cmd=cmd,
                msg=msg).run())
        
        note += value

        return note
