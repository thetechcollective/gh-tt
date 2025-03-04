from lazyload import Lazyload
import os
import sys
import subprocess
from pprint import pprint
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Gitter(Lazyload):
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    reguired_version = '2.55.0'
    verbose = False
    die_on_error = True
    workdir = os.getcwd()
    use_cache = False
    class_cache = {}  # Dictionary to store class cache data
    result = subprocess.run("git rev-parse --show-toplevel",
                            capture_output=True, text=True, shell=True)
    git_root = result.stdout.strip()
    if not git_root or result.returncode != 0:
        raise RuntimeError(f"Could not determine the git root directory")
    class_cache_file = f"{git_root}/.tt_cache"

    def __init__(self, cmd=str, die_on_error=None, msg=None, verbose=None, workdir=None):
        super().__init__()
        # se class defaults if not set
        if workdir == None:
            workdir = self.workdir
        if die_on_error == None:
            die_on_error = self.die_on_error
        if verbose == None:
            verbose = self.verbose
        self.set('cmd', cmd)
        self.set('msg', msg)
        self.set('die_on_error', die_on_error)
        self.set('verbose', verbose)
        self.set('workdir', workdir)
        self.set('cache', self.use_cache)

    def __verbose_print(self):

        if self.get('verbose'):
            # print an empty line
            print()
            if self.get('msg'):
                print(f"# {self.get('msg')}")
            print(f"$ {self.get('cmd')}")

    def run(self, cache=False):

        self.__verbose_print()

        if cache:
            cached_value = self.get_cache(self.get('workdir'), self.get('cmd'))
            if cached_value:
                if self.get('verbose'):
                    print(f"# NOTE! Returning cached value from previous run")
                    print(f"{cached_value}")
                return cached_value, None

        result = subprocess.run(
            self.get('cmd'), capture_output=True, text=True, shell=True, cwd=self.get('workdir'))

        if self.get('verbose'):
            print(f"{result.stdout.strip()}{result.stderr.strip()}")

        if self.get('die_on_error') and not result.returncode == 0:
            raise RuntimeError(f"{result.stderr}")
            sys.exit(1)

        output = result.stdout.strip()
        if cache:
            self.set_cache(self.get('workdir'), self.get('cmd'), output)
        return output, result

    @classmethod
    def get_cache(cls, workdir, cmd):
        if workdir not in cls.class_cache:
            return None
        if cmd not in cls.class_cache[workdir]:
            return None
        return cls.class_cache[workdir][cmd]

    @classmethod
    def set_cache(cls, workdir, cmd, value):
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
            print(
                f"WARNING: Could not save cache {cls.class_cache_file}", file=sys.stderr)
            pass

    @classmethod
    def verbose(cls, verbose=bool):
        cls.verbose = verbose

    @classmethod
    def validate_gh_version(cls, verbose=False):
        """Check if the user has sufficient access to the github cli

        Returns:
            [result (bool), status (str)] : True/'' if the validation is OK, False/Error message if the validation fails
        """
        gitter = Gitter(
            cmd="gh --version",
            msg="Check if the user has access to right version of gh CLI")
        [stdout, result] = gitter.run()

        # Validate that the version is => 2.55.0
        # The command returns something like this:
        #    gh version 2.65.0 (2025-01-06)
        #    https://github.com/cli/cli/releases/tag/v2.65.0

        version = stdout.split()[2]
        if version < cls.reguired_version:
            print(
                f"gh version {version} is not supported. Please upgrade to version {cls.reguired_version} or higher", file=sys.stderr)
            exit(1)

        return True

    @classmethod
    def validate_gh_scope(cls, scope=str):
        """Check if the user has sufficient access to the github cli"""

        [stdout, result] = Gitter(
            cmd="gh auth status",
            msg="Check if the user has sufficient access to update projects").run()

        # Valiadate that we have reaacce to projects
        # The command returns something like this:
        #  github.com
        #    ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
        #    - Active account: true
        #    - Git operations protocol: https
        #    - Token: gho_************************************
        #    - Token scopes: 'gist', 'read:org', 'project', 'repo', 'workflow'
        if f"'{scope}'" not in stdout:
            print(
                f"gh token does not have the required scope '{scope}'\nfix it by running:\n   gh auth refresh --scopes '{scope}'", file=sys.stderr)
            exit(1)

        return True
