import asyncio
import re
import sys
from enum import Enum, auto
from pathlib import Path

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.lazyload import Lazyload


class ReloadApproach(Enum):
    RELOAD = auto()
    NO_RELOAD = auto()

class ReleaseType(Enum):
    RELEASE = auto()
    PRERELEASE = auto()

class ExecutionMode(Enum):
    LIVE = auto()
    DRY_RUN = auto()

class Semver(Lazyload):
    """Class used to represent the semver state of git repository"""

    def __init__(self, suffix: str | None = None, prefix: str | None = None, initial: str | None = None):
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
    
    def __load_tags(self, reload: ReloadApproach = ReloadApproach.NO_RELOAD):
        """This methos does some post-processing of the raw list of tags
        It categorizes the tags into semver categories: release, prerelease and other.
        Release are defined as tags that match the semver pattern without a suffix.
        Prerelease are defined as tags that match the semver pattern with a suffix.
        Other are defined as tags that do not match the semver pattern.

        Args:
            reload (bool): If True, it will ignore any previously loaded tags and re-read the tags from the git repository.

        Loads:
            - semver_tags: A dictionary with the semver tags categorized into release, prerelease and other.
            - current_release: An array containing a three level interger array as key, and the current release semver tag.
            - next_release_major: The next major release semver tag.
            - next_release_minor: The next minor release semver tag.
            - next_release_patch: The next patch release semver tag.
            - current_prerelease: An array containing a three level interger array as key, and the current prerelease semver tag.
            - next_prerelease_major: The next major prerelease semver tag.
            - next_prerelease_minor: The next minor prerelease semver tag.
            - next_prerelease_patch: The next patch prerelease semver tag.    

        Returns:
            None

        Raises:
            None
        """

        if reload is ReloadApproach.RELOAD:
            self.props.pop('tags')

        asyncio.run(self._assert_props(['tags']))

        tags = self.get('tags').split('\n')
        semver_pattern = re.compile(r'^(.*?)(\d+)\.(\d+)\.(\d+)(.*)$')

        semver_tags = {}
        semver_tags['release'] = {}
        semver_tags['prerelease'] = {}
        semver_tags['other'] = {}
        

        for tag in tags:
            category = 'other'
            match = semver_pattern.search(tag)
            if match:
                category = 'prerelease' if match.group(5) else 'release'
                
                semver_tags[category][tuple(map(int, [match.group(2), match.group(3), match.group(4)]))] = tag
                continue
            
            # If it doesn't match the semver pattern, we categorize it as 'other'
            semver_tags['other'][tag] = tag



        for category in ['release', 'prerelease']:

            sorted_keys = sorted(semver_tags[category].keys())
            curcatkey = f"current_{category}"

            if len(sorted_keys) == 0:
                initial = self.get('initial')
                self.set(curcatkey, [tuple(map(int, initial.split('.'))), None])
            else:
                self.set(f"current_{category}", [sorted_keys[-1], semver_tags[category][sorted_keys[-1]]])

            curcatkey = f"current_{category}"
            major = f"{self.props[curcatkey][0][0]+1}.0.0"
            minor = f"{self.props[curcatkey][0][0]}.{self.props[curcatkey][0][1]+1}.0"
            patch = f"{self.props[curcatkey][0][0]}.{self.props[curcatkey][0][1]}.{self.props[curcatkey][0][2]+1}"
            
            self.set(f"next_{category}_major", major)
            self.set(f"next_{category}_minor", minor)
            self.set(f"next_{category}_patch", patch)

        # convert the tuple keys to string for JSON serialization
        for category in ['release', 'prerelease']:
            if category in semver_tags:
                # Convert tuple keys to comma-separated string without spaces or parentheses
                semver_tags[category] = {",".join(map(str, k)): v for k, v in semver_tags[category].items()}

        self.props['semver_tags'] = semver_tags

    def get_current_semver(self, release_type: ReleaseType = ReleaseType.RELEASE):
        """Returns the current semver tag"""

        self.__load_tags()

        if release_type is ReleaseType.PRERELEASE:
            if 'current_prerelease' not in self.props:
                return None
            return self.props['current_prerelease'][1]
        
        if 'current_release' not in self.props:
            return None
            sys.exit(0)
        return self.props['current_release'][1]

    
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

        self.__load_tags()

        if level not in ['major', 'minor', 'patch']:
            print(f"Invalid level '{level}'. Must be one of: major, minor, patch.", file=sys.stderr)
            sys.exit(1)

        if initial is not None:
            if not re.match(r'^\d+\.\d+\.\d+$', initial):
                print(f"⛔️ ERROR: Invalid initial version format '{initial}'. Must be in the format 'X.Y.Z' where X, Y, Z are integers.", file=sys.stderr)
                sys.exit(1)
        else:
            initial = self.get('initial')

        if prefix is None:
            prefix = self.get('prefix')

        if release_type is ReleaseType.PRERELEASE:
            if suffix is None:
                suffix = self.get('suffix')
        else:
            suffix = ''

        message = f"\n{message}" if message else ""

        pre = 'pre' if release_type else ''

        lookup_next =    f"next_{pre}release_{level}"
        lookup_current = f"current_{pre}release"


        next_tag = f"{self.get('prefix')}{self.get(lookup_next)}{suffix}"    


        cmd = f"git tag -a -m \"{next_tag}\nBumped {level} from version '{self.get(lookup_current)[1]}' to '{next_tag}'{message}\" {next_tag}"

        if execution_mode is ExecutionMode.DRY_RUN:
            print(f"{cmd}")
            return cmd
        
        [value,_] = asyncio.run(Gitter(
            cmd=cmd,
            msg=f"Bumping {level} from version '{self.get(lookup_current)[1]}' to '{next_tag}'"
        ).run())
        return {next_tag}
    

    
    def list(self, release_type: ReleaseType = ReleaseType.RELEASE):
        """Lists the semver tags in the repository to stdout sorted by major, minor, patch."""
        self.__load_tags()

        category = 'prerelease' if release_type is ReleaseType.PRERELEASE else 'release'
        
        temp = {tuple(map(int, k.split(','))): v for k, v in self.props['semver_tags'][category].items()}
        for k in sorted(temp.keys()):
            print(temp[k])
            
    
    def note(self, prerelease: ReleaseType = ReleaseType.RELEASE, filename: str | None = None) -> str:
        """Generates a release note either for a release or a prerelease, based on the set of current semver tags.

        Args:
            prerelease (bool): If True, it will generate a note based on (current_release..current_prerelease). 
                               If False it will generate a note based on (previous_release..current_release)
                               Defaults to False.
            filename (str): If provided, the note will be written to this file. If None, it will be printed to stdout.
        
        Returns:
            str: The markdown note of changes between the two references.

        Raises:
            SystemExit(1): If the logical references are not valid tags in the git repo

        """

        self.__load_tags()

        if prerelease is ReleaseType.PRERELEASE:
           from_ref = self.get_current_semver()
           to_ref = self.get_current_semver(release_type=ReleaseType.PRERELEASE)
        else:
              sorted_keys = sorted(self.get('semver_tags')['release'].keys())
              previous_release = self.get('semver_tags')['release'][sorted_keys[-2]]

              from_ref = previous_release
              to_ref = self.get_current_semver()

        note = self.note_md(from_ref=from_ref, to_ref=to_ref)

        if filename is not None:
            # make sure the directory exists
            directory = Path.parent(filename)
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

        self.__load_tags()

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


        

        