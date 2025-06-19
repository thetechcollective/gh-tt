from lazyload import Lazyload
import os
import sys
import subprocess
from pprint import pprint
import json
import asyncio

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Gitter(Lazyload):
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    required_version = '2.55.0'
    verbose = False
    die_on_error = True
    workdir = os.getcwd()
    use_cache = False
    fetched = False  # Flag to indicate if the repository has been fetched
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

    async def run(self, cache=False):

        self.__verbose_print()

        if cache:
            cached_value = self.get_cache(self.get('workdir'), self.get('cmd'))
            if cached_value:
                if self.get('verbose'):
                    print(f"# NOTE! Returning cached value from previous run")
                    print(f"{cached_value}")
                return cached_value, None

        proc = await asyncio.create_subprocess_shell(
            self.get('cmd'),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        stdout = stdout.decode().strip()
        stderr = stderr.decode().strip()

        if self.get('verbose'):
            print(f"{stdout}{stderr}")

        if self.get('die_on_error') and not proc.returncode == 0:
            raise RuntimeError(f"{stderr}")

        if cache:
            self.set_cache(self.get('workdir'), self.get('cmd'), stdout)
        return stdout, proc

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
    async def validate_gh_version(cls):
        """Check if the user has a sufficiently recent version of the GitHub CLI.
        Exits the program if the version is not supported.

        Returns:
            True if validation succeeds.
        """

        [stdout, _] = await Gitter(
                cmd="gh --version",
                msg="Check if the user has access to right version of gh CLI").run()
        
        # Validate that the version is => 2.55.0
        # The command returns something like this:
        #    gh version 2.65.0 (2025-01-06)
        #    https://github.com/cli/cli/releases/tag/v2.65.0

        version = stdout.split()[2]
        if version < cls.required_version:
            print(
                f"gh version {version} is not supported. Please upgrade to version {cls.required_version} or higher", file=sys.stderr)
            sys.exit(1)

        return True

    @classmethod
    async def validate_gh_scope(cls, scope=str) -> bool:
        """
        Check if the user has sufficient access to the GitHub CLI. If not, exits.

        Returns:
            True if the user has sufficient access.
        """

        [stdout, _] = await Gitter(
            cmd="gh auth status",
            msg="Check if the user has sufficient GH CLI permissions").run()

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
            sys.exit(1)

        return True

    @classmethod
    async def fetch(cls, prune=False, again=False):
        """Fetch """

        if cls.fetched and not again:
            return True

        msg = "Fetch all branches and tags from all remotes"

        prune_switch = "--prune --prune-tags" if prune else ""
        if prune:
            msg += " and prune local branches and tags)"

        [_, _] = await Gitter(
            cmd=f"git fetch --tags --all -f {prune_switch}",
            msg=f"{msg}").run()

        cls.fetched = True

        return True
