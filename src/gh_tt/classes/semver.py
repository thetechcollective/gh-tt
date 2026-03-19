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

@dataclass(frozen=True)
class SemverVersion:
    major: int
    minor: int
    patch: int
    prerelease: str | None = None  # In SemVer, this is the entire string after the hyphen
    build: str | None = None       # In SemVer, this is the entire string after the plus
    
    def __post_init__(self):
        pass
            
    # Removed redundant _compare_prerelease and _compare_build methods
    # Now directly using _compare_identifiers in _compare_prerelease_components and _compare_build_components
        
    def _compare_identifiers(self, self_identifiers: str, other_identifiers: str) -> bool:
        """Generic method to compare dot-separated identifiers according to SemVer spec.
        Works for both prerelease and build metadata.
        
        Args:
            self_identifiers: The first identifiers string
            other_identifiers: The second identifiers string
            
        Returns:
            True if self_identifiers < other_identifiers, False otherwise
        """
        self_parts = self_identifiers.split('.')
        other_parts = other_identifiers.split('.')
        
        # Compare each identifier
        for i in range(min(len(self_parts), len(other_parts))):
            self_is_numeric = self_parts[i].isdigit()
            other_is_numeric = other_parts[i].isdigit()
            
            # If both identifiers are numeric, compare numerically
            if self_is_numeric and other_is_numeric:
                self_num = int(self_parts[i])
                other_num = int(other_parts[i])
                if self_num != other_num:
                    return self_num < other_num
                continue
                
            # If only one is numeric, numeric has lower precedence
            if self_is_numeric:
                return True  # self is lower
            if other_is_numeric:
                return False  # self is higher
                
            # Otherwise compare lexically
            if self_parts[i] != other_parts[i]:
                return self_parts[i] < other_parts[i]
        
        # If we get here, one string is a prefix of the other
        # The shorter one is the smaller version
        return len(self_parts) < len(other_parts)
        
        
    def __lt__(self, other):
        """Compare two SemVer versions according to SemVer 2.0.0 specification.
        
        Args:
            other: The other SemverVersion to compare against
            
        Returns:
            True if self < other, False otherwise
        """
        if not isinstance(other, SemverVersion):
            return NotImplemented
            
        # Compare major.minor.patch numerically
        return self._compare_core_version(other)
            
    def _compare_core_version(self, other):
        """Compare the core version components (major.minor.patch).
        
        Args:
            other: The other SemverVersion to compare against
            
        Returns:
            True if self < other based on core version,
            False if self > other or equal based on core version
            If equal, calls _compare_prerelease_components to continue comparison
        """
        # First compare major.minor.patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
            
        # If core versions are equal, compare prerelease components
        return self._compare_prerelease_components(other)
    
    def _compare_prerelease_components(self, other):
        """Compare the prerelease components after core versions are found equal.
        
        Args:
            other: The other SemverVersion to compare against
            
        Returns:
            True if self < other based on prerelease,
            False if self > other or equal based on prerelease
            If equal, calls _compare_build_components to continue comparison
        """
        # Handle prerelease special case: a version WITH prerelease is LOWER than one WITHOUT
        if self.prerelease is None and other.prerelease is not None:
            return False  # self is higher
        if self.prerelease is not None and other.prerelease is None:
            return True   # self is lower
            
        # If both have prerelease identifiers, compare them
        if self.prerelease is not None and other.prerelease is not None and self.prerelease != other.prerelease:
            return self._compare_identifiers(self.prerelease, other.prerelease)
                
        # If prerelease components are equal, compare build components
        return self._compare_build_components(other)
        
    def _compare_build_components(self, other):
        """Compare the build components after prerelease components are found equal.
        
        Args:
            other: The other SemverVersion to compare against
            
        Returns:
            True if self < other based on build,
            False if self > other or equal based on build
        """
        # For versions that are otherwise identical, a version with build metadata
        # should sort higher than one without
        if self.build is None and other.build is not None:
            return True  # self is lower (no build < has build)
        if self.build is not None and other.build is None:
            return False  # self is higher (has build > no build)
            
        # If both have build metadata, compare them
        if self.build is not None and other.build is not None and self.build != other.build:
            return self._compare_identifiers(self.build, other.build)
            
        # If we get here, both are None, so they're equal
        return False

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease is not None:
            version += f"-{self.prerelease}"
        if self.build is not None:
            version += f"+{self.build}"
        return version
    
    def bump_major(self) -> SemverVersion:
        return SemverVersion(self.major + 1, 0, 0, None, None)
    
    def bump_minor(self) -> SemverVersion:
        return SemverVersion(self.major, self.minor + 1, 0, None, None)
    
    def bump_patch(self) -> SemverVersion:
        return SemverVersion(self.major, self.minor, self.patch + 1, None, None)
    
    def bump_prerelease(self) -> SemverVersion:
        """Bump prerelease version according to SemVer.
        
        Returns:
            A new SemverVersion with bumped prerelease
        """
            
        # Parse existing prerelease if any
        if self.prerelease is not None:
            # Check if the prerelease contains digits at the end (like "rc1")
            import re
            match = re.search(r'([a-zA-Z-]+)(\d+)$', self.prerelease)
            if match:
                # Format is like "rc1", increment the number
                prefix, number = match.groups()
                new_prerelease = f"{prefix}{int(number) + 1}"
            elif self.prerelease[-1].isdigit():
                # Try to find a numeric part at the end to increment
                parts = self.prerelease.split('.')
                if parts[-1].isdigit():
                    # Increment the last numeric part
                    parts[-1] = str(int(parts[-1]) + 1)
                    new_prerelease = '.'.join(parts)
                else:
                    # This shouldn't happen with proper semver, but just in case
                    new_prerelease = f"{self.prerelease}1"
            else:
                # Add a 1 if no numeric part exists
                new_prerelease = f"{self.prerelease}1"
                
            return SemverVersion(self.major, self.minor, self.patch, new_prerelease, None)
            
        # Create a new prerelease with a hardcoded "alpha1" identifier
        # We no longer support configurable suffixes
        return SemverVersion(self.major, self.minor, self.patch, "alpha1", None)
    
    def bump_build(self, *, include_sha: bool = True) -> SemverVersion:
        """Bump build version according to SemVer.
        
        Args:
            include_sha: Whether to include short SHA in build number (default=True)
            
        Returns:
            A new SemverVersion with bumped build
        """
        # Get the short SHA if needed
        short_sha = None
        if include_sha:
            import contextlib
            with contextlib.suppress(Exception):
                # Get the current commit SHA and take first 7 characters
                full_sha = Gitter.get_commit_sha()
                if full_sha:
                    short_sha = full_sha[:7]  # Use first 7 chars for short SHA
                
        # Parse existing build if any
        sequence = 1
        if self.build is not None:
            parts = self.build.split('.')
            # Try to extract the sequence number
            if parts[0].isdigit():
                sequence = int(parts[0]) + 1
        
        # Create the new build string - always include SHA if available
        new_build = f"{sequence}.{short_sha}" if short_sha and include_sha else f"{sequence}"
        
        # Return a new SemverVersion with the updated build
        return SemverVersion(self.major, self.minor, self.patch, self.prerelease, new_build)
    
    def is_prerelease(self):
        """Check if this version is a prerelease version."""
        return self.prerelease is not None
    
    @classmethod
    def from_string(cls, version_str: str) -> SemverVersion:
        """Parse a version string according to SemVer specification.
        
        Format: <major>.<minor>.<patch>[-<prerelease>][+<build>]
        where <major>, <minor>, and <patch> are non-negative integers without leading zeros.
        """
        # Exact regex for matching the SemVer format
        semver_pattern = r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        
        match = re.match(semver_pattern, version_str)
        
        if not match:
            raise ValueError(f"Invalid semver format: {version_str}")
        
        # Simply use the values directly from the match groups
        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=match.group('prerelease'),
            build=match.group('build')
        )
    
@dataclass(frozen=True)
class SemverTag:
    version: SemverVersion
    prefix: str | None = None
    sha: str | None = None

    def __str__(self) -> str:
        prefix_str = self.prefix if self.prefix is not None else ''
        return f'{prefix_str}{self.version}'
    
    def __lt__(self, other) -> bool:
        assert isinstance(other, SemverTag)
        
        return self.version < other.version
    
    @classmethod
    def from_string(cls, tag: str, prefix: str | None, sha: str | None = None) -> SemverTag | None:
        version_str = tag
        if prefix is not None and prefix:
            version_str = tag.split(prefix)[1]

        try:
            version = SemverVersion.from_string(version_str)
        except ValueError:
            return None

        return cls(version, prefix, sha)

class Semver(Lazyload):
    """Class used to represent the semver state of git repository"""

    def __init__(self, prefix: str | None = None, initial: str | None = None, tag_string: str | None = None):
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
        asyncio.run(semver._assert_props(['tags', 'tag_shas']))
        semver.set('semver_tags', semver._parse_tags(
            semver.get('tags'), 
            semver.get('prefix'),
            semver.get('tag_shas')
        ))

        return semver
    
    def _parse_tags(self, tag_string: str, prefix: str | None, tag_shas_string: str | None = None) -> dict:
        tags = tag_string.split('\n') if tag_string else []
        
        # Parse tag SHAs if available
        tag_sha_map = {}
        if tag_shas_string:
            for line in tag_shas_string.split('\n'):
                if line.strip():
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        sha, tag_name = parts
                        tag_sha_map[tag_name] = sha

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

            # Create tag with SHA information upfront
            sha = tag_sha_map.get(tag_str)
            semver_tag = SemverTag.from_string(tag_str, prefix, sha)
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
    

    def _get_next_semvers(self, current_release: SemverVersion | None, current_prerelease: SemverVersion | None) -> dict:
        result = {
            'next_release_major': current_release.bump_major() if current_release is not None else None,
            'next_release_minor': current_release.bump_minor() if current_release is not None else None,
            'next_release_patch': current_release.bump_patch() if current_release is not None else None,
            'next_prerelease_major': current_prerelease.bump_major().bump_prerelease() if current_prerelease is not None else current_release.bump_major().bump_prerelease(),
            'next_prerelease_minor': current_prerelease.bump_minor().bump_prerelease() if current_prerelease is not None else current_release.bump_minor().bump_prerelease(),
            'next_prerelease_patch': current_prerelease.bump_patch().bump_prerelease() if current_prerelease is not None else current_release.bump_patch().bump_prerelease(),
            'next_prerelease_prerelease': current_prerelease.bump_prerelease() if current_prerelease is not None else current_release.bump_prerelease(),
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
            prefix: str | None = None,
            release_type: ReleaseType = ReleaseType.RELEASE,
            execution_mode: ExecutionMode = ExecutionMode.LIVE
        ):

        assert level in ['major', 'minor', 'patch', 'prerelease']

        if prefix is None:
            prefix = self.get('prefix')

        message = f"\n{message}" if message else ""

        current_version = self.get_current_semver().version if self.get_current_semver() is not None else None
        current_prerelease_version = self.get_current_semver(ReleaseType.PRERELEASE).version if self.get_current_semver(ReleaseType.PRERELEASE) is not None else None

        self._get_next_semvers(current_version, current_prerelease_version)
        key = f'next_{release_type}_{level}'
        next_tag = f'{prefix}{self.get(key)}'


        from_version = self.get_current_semver(release_type)
        if from_version is None and release_type is ReleaseType.PRERELEASE:
            from_version = self.get_current_semver()

        cmd = f"git tag -a -m \"{next_tag}\nBumped {level} from version '{from_version}' to '{next_tag}'{message}\" {next_tag}"

        assert prefix is None or (prefix is not None and prefix in next_tag)

        if execution_mode is ExecutionMode.DRY_RUN:
            print(f"{cmd}")
            return cmd
        
        assert execution_mode is ExecutionMode.LIVE
        asyncio.run(Gitter(
            cmd=cmd,
            msg=f"Bumping {level} from version '{self.get_current_semver(release_type)}' to '{next_tag}'"
        ).run())

        return {next_tag}
    

    
    def list(self, release_type: ReleaseType = ReleaseType.RELEASE, filter_type: str = 'release', *, show_sha: bool = False):
        """Lists the semver tags in the repository to stdout sorted by major, minor, patch.
        
        Args:
            release_type: Deprecated. Use filter_type instead.
            filter_type: Which types of tags to display:
                - 'release': Only show release versions
                - 'prerelease': Only show prerelease versions
                - 'other': Only show non-semver version tags
                - 'all': Show all tags
            show_sha: If True, also display the SHA for each tag
        """
        current_tags = self.get('semver_tags')['current']
        
        # For backwards compatibility
        if release_type is ReleaseType.PRERELEASE and filter_type == 'release':
            filter_type = 'prerelease'
            
        # Determine which categories to display
        categories_to_show = []
        if filter_type == 'all':
            categories_to_show = ['release', 'prerelease', 'other']
        else:
            categories_to_show = [filter_type]
            
        # Display tags for each selected category
        for category in categories_to_show:
            if current_tags.get(category):
                if len(categories_to_show) > 1:
                    print(f"\n--- {category.capitalize()} tags ---")
                # Reverse the sorted list to show highest versions first (most recent on top)
                tags = sorted(current_tags[category], reverse=True)
                for tag in tags:
                    if show_sha and hasattr(tag, 'sha') and tag.sha:
                        print(f"{tag} {tag.sha}")
                    else:
                        print(tag)
            
    def note(self, release_type: ReleaseType = ReleaseType.RELEASE, filename: str | None = None, from_ref: str | None = None, to_ref: str | None = None) -> str:
        """Generates a release note either for a release or a prerelease, based on the set of current semver tags.

        Args:
            release_type (enum): If PRERELEASE, it will generate a note based on (current_release..current_prerelease). 
                               If RELEASE it will generate a note based on (previous_release..current_release)
                               Defaults to RELEASE.
            filename (str): If provided, the note will be written to this file. If None, it will be printed to stdout.
            from_ref (str): Optional starting reference for the release note. If None, defaults based on release_type.
            to_ref (str): Optional ending reference for the release note. If None, defaults based on release_type.
        
        Returns:
            str: The markdown note of changes between the two references.

        Raises:
            SystemExit(1): If the logical references are not valid tags in the git repo

        """
        # Determine from_ref if not explicitly provided
        from_ref = self._determine_from_ref(from_ref, release_type)
        
        # Determine to_ref if not explicitly provided  
        if to_ref is None:
            if release_type is ReleaseType.PRERELEASE:
                to_ref = self.get_current_semver(release_type=ReleaseType.PRERELEASE)
            else:
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
                
    def _determine_from_ref(self, from_ref: str | None, release_type: ReleaseType) -> str:
        """Helper method to determine the from_ref based on release type if not explicitly provided

        Args:
            from_ref (str | None): Explicitly provided from_ref or None
            release_type (ReleaseType): The type of release (RELEASE or PRERELEASE)

        Returns:
            str: The determined from_ref

        Raises:
            SystemExit(1): If no valid from_ref can be determined
        """
        if from_ref is not None:
            return from_ref
            
        if release_type is ReleaseType.PRERELEASE:
            return self.get_current_semver()
            
        # Handle RELEASE type
        releases = sorted(self.get('semver_tags')['current']['release'])
        
        if len(releases) > 1:
            return releases[-2]  # Get the second-to-last release
        
        # No previous release found, try to find root commit
        print("Could not find previous release tag when assembling changes for the note. Attempting to find a root commit instead.")
        [root_commit, _] = asyncio.run(Gitter(
            cmd='git rev-list --max-parents=0 HEAD',
            msg='Find root commits'
        ).run())

        if root_commit.find('\n') != -1:
            print("Found multiple root commits. To create a note without any previous releases and multiple root commits, please create an explicit initial tag (e.g. 0.0.0). All changes from this ref will be included in the release note.", file=sys.stderr)
            sys.exit(1)

        print("Found root commit. The release note will include all changes since the root commit, excluding the root commit.")
        return root_commit.strip()
    

    
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
