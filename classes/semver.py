import asyncio
import re


from classes.lazyload import Lazyload


class Semver(Lazyload):
    """Class used to represent the semver state of git repository"""

    # Class constants
    config_file_name = ".semver.config"
    _verbose = False
    props = {
        'config_file': None,
        'prefix': None,
        'initial': None,
        'suffix': None,
        'workdir': None,
        'git_root': None,
        'config': None,
        'semver_tags': None,
        'current_semver': None,
        'next': None,
    }

    # Class variables


    # DELETED
    # def __run_git(self, cmd=str, die_on_error=True) -> list[str, subprocess.CompletedProcess]:
    #    self.verbose_print(f"⚙️  {cmd}")
    #    result = subprocess.run(
    #    cmd, capture_output=True, text=True, shell=True, cwd=self.props['workdir'])
    #    if result.returncode != 0 and die_on_error:
    #        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
    #        sys.exit(1)
    #    return [result.stdout.strip(), result]    
          
    # Instance methods
    def __init__(self, workdir=None):
        super().__init__()

        self.__read_semver_tags()
        self.__read_semver_config()

    def __read_semver_tags(self):

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
                if match.group(5):
                    category = 'prerelease'
                else:
                    category = 'release'
                
                semver_tags[category][tuple(map(int, [match.group(2), match.group(3), match.group(4)]))] = tag
                continue
            else:
                # If it doesn't match the semver pattern, we categorize it as 'other'
                semver_tags['other'][tag] = tag


        self.set('semver_tags', semver_tags)

        for category in ['release', 'prerelease']:

            if semver_tags[category] :
                sorted_keys = sorted(semver_tags[category].keys())
                self.set(f"current_{category}", sorted_keys[-1])
                self.set(f"current_{category}_tag", semver_tags[category][sorted_keys[-1]])
        
        # DELETE
        #if not self.props['current_semver']:
        #    self.__set_current_semver_from_initial()
        #self.__set_next_versions()

    def __set_current_semver_from_initial(self):

        if self.props['initial'] == None:
            self.props['initial'] = '0.0.0'
        try:
            self.props['current_semver'] = tuple(map(int, self.props['initial'].split('.')))
        except Exception as e:
            raise ValueError(f"Failed to parse initial version, doesn't look like a three-level integer: {e}")
        
        suffix = ''
        if self.props['suffix'] is not None:
            suffix = self.props['suffix']
            
        self.set('current_tag', f"{self.props['prefix']}{self.props['initial']}{suffix}")
    

    def __set_next_versions(self):    
        # Bump major, reset minor and patch
        next = {}
        next['major'] = f"{self.props['current_semver'][0] + 1}.0.0"
        # Leave major, bump minor, reset patch
        next['minor'] = f"{self.props['current_semver'][0]}.{self.props['current_semver'][1] + 1}.0"
        # Leave major and minor, bump patch
        next['patch'] = f"{self.props['current_semver'][0]}.{self.props['current_semver'][1]}.{self.props['current_semver'][2] + 1}"

        self.set('next', next)

    
     
    def __read_semver_config(self):
        """Read the .semver.config file and store the configuration as a dictionary"""
        
        config = {}
        # The config_file may not exist - we don't care. Just continue and return an empty dict
        [output,_] = self.__run_git(f"git config list --file {self.props['config_file']}", die_on_error=False)

        try:
            config = {line.split('=')[0]: line.split('=')[1] for line in output.split('\n') if '=' in line}
        except Exception:
            pass

        self.set('config', config)

        self.set('prefix', config.get('semver.prefix', ''))
        self.set('initial', config.get('semver.initial', '0.0.0'))
        self.set('suffix', config.get('semver.suffix', ''))
        if self.props['semver_tags'].keys().__len__() == 0:
            self.__set_current_semver_from_initial()
            self.__set_next_versions()
    
    def set_config(self, prefix=None, initial=None, suffix=None):
        """Set the configuration in the .semver.config file"""

        args = {'prefix': prefix, 'initial': initial, 'suffix': suffix}
        for setting in args.keys():
            if args[setting]:
                [_,_] = self.__run_git(f"git config --file {self.props['config_file']} semver.{setting} {args[setting]}")
        self.__read_semver_config()
        
  
    def bump(self, level=str, message=None, suffix=None):
        cmd = self.get_git_tag_cmd(level, message, suffix)
        [_,_] = self.__run_git(cmd)
        self.__read_semver_tags()
        return self.props['current_tag']

    def get_git_tag_cmd(self, level=str, message=None, suffix=None):
        if message:
            message = f"\n{message}"
        else:
            message = ""

        if suffix:
            suffix = f"{suffix}"
        else:
            if self.props['suffix']:
                suffix = f"{self.props['suffix']}"
            else:
                suffix = ""

        next_tag = f"{self.props['prefix']}{self.props['next'][level]}{suffix}"

        return f"git tag -a -m \"{next_tag}\nBumped {level} from version '{self.props['current_tag']}' to '{next_tag}'{message}\" {next_tag}"

    def verbose_print(self, message:str):
        """Prints the message if verbose is enabled"""
        if self._verbose:
            print(message)

    def set(self, prop:str, value):
        self.props[prop] = value
        if self._verbose:
            print(f"🏷️  '{prop}': {self.props[prop]}")
    
    @classmethod
    def verbose(cls, verbose:bool = True):
        cls._verbose = verbose