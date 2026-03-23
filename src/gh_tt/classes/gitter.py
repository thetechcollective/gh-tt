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

    _fetch_lock = asyncio.Lock()

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
    
    @classmethod
    def set_verbose(cls, *, value: bool):
        cls.verbose = value


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
    def version(cls):
        print(asyncio.run(cls()._run("version_context")))

    @classmethod
    def get_commit_sha(cls):
        """Get current commit SHA"""
        return asyncio.run(cls()._run("get_commit_sha"))
