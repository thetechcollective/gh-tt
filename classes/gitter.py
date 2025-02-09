import os
import sys
import subprocess
from pprint import pprint
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

class Gitter:
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    
    props = {}       # Dictionary to store class instance properties
    class_cache = {} # Dictionary to store class cache data
    result = subprocess.run("git rev-parse --show-toplevel", capture_output=True, text=True, shell=True)
    git_root = result.stdout.strip()
    if not git_root or result.returncode != 0:
        raise RuntimeError(f"Could not determine the git root directory")
    class_cache_file = f"{git_root}/.tt_cache'"
    
    def __init__(self, cmd=str, die_on_error=True, msg=None, verbose=False, workdir=None):    
        if workdir == None:
            workdir = os.getcwd()
        
        self.set('cmd', cmd)
        self.set('die_on_error', die_on_error)
        self.set('msg', msg)
        self.set('verbose', verbose)
        self.set('workdir', workdir)
                
    def set(self, key, value):
        self.props[key] = value
        return self.props[key]
    
    def get(self, key):
        if key not in self.props:
            raise KeyError(f"Key {key} not found in properties")
            sys.exit(1)
        return self.props[key]
        
    def __verbose_print(self):

        if self.get('verbose'):
            if self.get('msg'):
                print (f"# {self.get('msg')}")
            print (f"$ {self.get('cmd')}")
            
    def run(self, cache=False):
        
        self.__verbose_print()
        
        if cache:
            cached_value = self.get_cache(self.get('workdir'), self.get('cmd'))
            if cached_value:
                if self.get('verbose'):
                    print(f"# Returned cached value from previous run\n")
                return cached_value, None
                    
        result = subprocess.run(
            self.get('cmd'), capture_output=True, text=True, shell=True, cwd=self.get('workdir'))
        if self.get('die_on_error') and not result.returncode == 0:
            raise RuntimeError(f"{result.stderr}")
            sys.exit(1)
        output = result.stdout.strip()    
        if cache:
            self.set_cache(self.get('workdir'), self.get('cmd'), output) 
        return output, result

    @classmethod
    def get_cache(cls, workdir, cmd ):
        if workdir not in cls.class_cache:
            return None
        if cmd not in cls.class_cache[workdir]:
            return None
        return cls.class_cache[workdir][cmd]
    
    @classmethod
    def set_cache(cls, workdir, cmd, value ):
        if workdir not in cls.class_cache:
            cls.class_cache[workdir] = {}
        cls.class_cache[workdir][cmd] = value
        return cls.class_cache[workdir][cmd]

    @classmethod
    def print_cache(cls):
        print(json.dumps(cls.class_cache, indent=4))
        
    @classmethod
    # read the cache from a file in the root of the repository `.tt_cache`
    # and load it into the class_cache
    def read_cache(cls):
        try:
            with open(cls.class_cache_file, 'r') as f:
                cls.class_cache = json.load(f)
        except FileNotFoundError:
            pass

    @classmethod
    # write the class_cache to a file in the root of the repository `.tt_cache`
    def write_cache(cls):
        try:
            with open(cls.class_cache_file, 'w') as f:
                json.dump(cls.class_cache, f, indent=4)
        except FileNotFoundError:
            print(f"WARNING: Could not save cache {cls.class_cache_file}", file=sys.stderr)
            pass
            