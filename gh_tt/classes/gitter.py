import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import ClassVar

from gh_tt.classes.lazyload import Lazyload


class Gitter(Lazyload):
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    required_version = '2.55.0'
    verbose = False
    die_on_error = True
    workdir = Path.cwd()
    use_cache = False
    fetched = False  # Flag to indicate if the repository has been fetched
    class_cache: ClassVar[dict] = {}  # Dictionary to store class cache data

    git_path = shutil.which('git')
    assert git_path is not None, "Git not found on PATH. Git is required for gh-tt to work. To proceed, install git."

    result = subprocess.run(
        [git_path, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    git_root = result.stdout.strip()
    if not git_root or result.returncode != 0:
        raise RuntimeError("Could not determine the git root directory")
    class_cache_file = Path(git_root) / ".tt_cache"

    def __init__(self, cmd=str, die_on_error=None, msg=None, verbose=None, workdir=None):
        super().__init__()
        # se class defaults if not set
        if workdir is None:
            workdir = self.workdir
        if die_on_error is None:
            die_on_error = self.die_on_error
        if verbose is None:
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

    async def run(self, *, cache=False):

        self.__verbose_print()

        if cache:
            cached_value = self.get_cache(self.get('workdir'), self.get('cmd'))
            if cached_value:
                if self.get('verbose'):
                    print("# NOTE! Returning cached value from previous run")
                    print(f"{cached_value}")
                return cached_value, None
            
        process = await asyncio.create_subprocess_shell(
            cmd=self.get('cmd'),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.get('workdir')
        )

        stdout, stderr = await process.communicate()

        stdout = stdout.decode().rstrip()
        stderr = stderr.decode().rstrip()

        if self.get('verbose'):
            print(f"{stdout}{stderr}")

        if self.get('die_on_error') and process.returncode != 0:
            raise RuntimeError(f"{stderr}")

        if cache:
            self.set_cache(self.get('workdir'), self.get('cmd'), stdout)
        
        result = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        }

        return stdout, result
    
    @classmethod
    def set_verbose(cls, *, value: bool):
        cls.verbose = value

    @classmethod
    def get_cache(cls, workdir, cmd):
        workdir_str = str(workdir)
        
        if workdir_str not in cls.class_cache:
            return None
        if cmd not in cls.class_cache[workdir_str]:
            return None
        return cls.class_cache[workdir_str][cmd]

    @classmethod
    def set_cache(cls, workdir, cmd, value):
        workdir_str = str(workdir)

        if workdir_str not in cls.class_cache:
            cls.class_cache[workdir_str] = {}
        cls.class_cache[workdir_str][cmd] = value
        return cls.class_cache[workdir_str][cmd]

    @classmethod
    def print_cache(cls):
        print(json.dumps(cls.class_cache, indent=4))

    @classmethod
    # read the cache from a file in the root of the repository `.tt_cache`
    # and load it into the class_cache
    def read_cache(cls):
        try:
            with Path.open(cls.class_cache_file) as f:
                cls.class_cache = json.load(f)
        except FileNotFoundError:
            pass

    @classmethod
    # write the class_cache to a file in the root of the repository `.tt_cache`
    def write_cache(cls):
        try:
            with Path.open(cls.class_cache_file, 'w') as f:
                json.dump(cls.class_cache, f, indent=4)
        except FileNotFoundError:
            print(
                f"WARNING: Could not save cache {cls.class_cache_file}", file=sys.stderr)

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
        if version < cls.required_version:
            print(
                f"gh version {version} is not supported. Please upgrade to version {cls.required_version} or higher", file=sys.stderr)
            exit(1)

        return True

    @classmethod
    def validate_gh_scope(cls, scope: str):
        """Check if the user has sufficient access to the github cli"""

        stdout = asyncio.run(cls()._run("validate_gh_scope"))

        # The command returns something like this:
        #  github.com
        #    ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
        #    - Active account: true
        #    - Git operations protocol: https
        #    - Token: gho_************************************
        #    - Token scopes: 'gist', 'read:org', 'project', 'repo', 'workflow'
        
        if "Token: ghs" in stdout:
            # When authenticated with a ghs (server-to-server) token
            # (for example, a GitHub App Installation Token),
            # `gh auth status` does not output token scopes. Thus,
            # the function always fails. As permissions for GitHub apps
            # are managed in the App installation or in GitHub Actions,
            # we want this function to return True for ghs tokens.
            # See https://github.blog/engineering/platform-security/behind-githubs-new-authentication-token-formats/#identifiable-prefixes
            # for other token prefixes.
            return True


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
    async def fetch(cls, *, prune=False, again=False):
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
