import asyncio
import json
import os
import subprocess
import sys
from pprint import pprint

from gh_tt.classes.lazyload import Lazyload


class Gitter(Lazyload):
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    reguired_version = '2.55.0'
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

        result = subprocess.run(
            self.get('cmd'), capture_output=True, text=True, shell=True, cwd=self.get('workdir'))

        if self.get('verbose'):
            print(f"{result.stdout.rstrip()}{result.stderr.rstrip()}")

        if self.get('die_on_error') and not result.returncode == 0:
            raise RuntimeError(f"{result.stderr}")
            sys.exit(1)

        output = result.stdout.rstrip()
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
    def validate_gh_version(cls):
        """Check if the user has sufficient access to the github cli

        Returns:
            [result (bool), status (str)] : True/'' if the validation is OK, False/Error message if the validation fails
        """

        stdout = asyncio.run(cls()._run("validate_gh_version"))

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
    def validate_gh_scope(cls, scope: str):
        """Check if the user has sufficient access to the github cli"""

        stdout = asyncio.run(cls()._run("validate_gh_scope"))

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
    
    @classmethod
    def version(cls):
        print(asyncio.run(cls()._run("version_context")))

    @classmethod
    def get_commit_sha(cls):
        """Get current commit SHA"""
        return asyncio.run(cls()._run("get_commit_sha"))

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
