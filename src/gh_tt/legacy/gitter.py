import asyncio
import shutil
from pathlib import Path
from typing import ClassVar

from gh_tt.legacy.lazyload import Lazyload


class Gitter(Lazyload):
    """Class used to run sub process commands (optimized for git and gh commands).
        It supports using cached data from previous runs.
    """
    required_version = '2.55.0'
    die_on_error = True
    workdir = Path.cwd()
    use_cache = False
    fetched = False  # Flag to indicate if the repository has been fetched
    class_cache: ClassVar[dict] = {}  # Dictionary to store class cache data

    _fetch_lock = asyncio.Lock()

    git_path = shutil.which('git')
    assert git_path is not None, "Git not found on PATH. Git is required for gh-tt to work. To proceed, install git."


    def __init__(self, cmd=str, die_on_error=None, msg=None, workdir=None):
        super().__init__()
        # se class defaults if not set
        if workdir is None:
            workdir = self.workdir
        if die_on_error is None:
            die_on_error = self.die_on_error
        
        self.set('cmd', cmd)
        self.set('msg', msg)
        self.set('die_on_error', die_on_error)
        self.set('workdir', workdir)
        self.set('cache', self.use_cache)

    async def run(self):            
        process = await asyncio.create_subprocess_shell(
            cmd=self.get('cmd'),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.get('workdir')
        )

        stdout, stderr = await process.communicate()

        stdout = stdout.decode().rstrip()
        stderr = stderr.decode().rstrip()

        if self.get('die_on_error') and process.returncode != 0:
            raise RuntimeError(f"{stderr}")
        
        result = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        }

        return stdout, result

    @classmethod
    async def fetch(cls, *, prune=False, again=False):
        """Fetch """

        async with cls._fetch_lock:
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