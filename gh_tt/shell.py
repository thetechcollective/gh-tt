import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ShellError(Exception):
    cmd: str
    stdout: str
    stderr: str
    return_code: int

    def __str__(self) -> str:
        return f'Command failed with return code {self.return_code}\ncommand: {self.cmd}\nstdout: {self.stdout}\nstderr: {self.stderr}'


@dataclass
class ShellResult:
    stdout: str
    stderr: str
    return_code: int


async def run(cmd: list[str], *, cwd: Path | None = None, die_on_error: bool = True) -> ShellResult:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    stdout, stderr = await process.communicate()
    stdout = stdout.decode().rstrip()
    stderr = stderr.decode().rstrip()

    if die_on_error and process.returncode != 0:
        raise ShellError(cmd=cmd, stdout=stdout, stderr=stderr, return_code=process.returncode)

    return ShellResult(stdout=stdout, stderr=stderr, return_code=process.returncode)
