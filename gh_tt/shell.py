import asyncio
from collections.abc import Callable
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


async def poll_until(
    cmd: list[str],
    cwd: Path,
    predicate: Callable[[ShellResult], bool],
    timeout_seconds: int = 30,
    interval: int = 3,
) -> ShellResult | None:
    """Reruns the command until the predicate is true. Be careful when using with effectful functions.

    Naively reruns the `cmd` until the predicate is true or the timeout is reached.

    Args:
        cmd: The command to run.
        cwd: The working directory for the command.
        predicate: Callable returning a bool. Will be evaluated on every iteration.
            If the return value of the callable is false and the timeout is not
            reached, the `cmd` is called again.
        timeout_seconds: How long to keep retrying.
        interval: Amout of time between retries. Uses asyncio.sleep(), so may not be
            exact.

    Returns:
        A `ShellResult` if the predicate evaluates to True before the timeout.
        Returns `None` if the timeout is reached.
    """

    try:
        async with asyncio.timeout(timeout_seconds):
            while True:
                result = await run(cmd, cwd=cwd)
                if predicate(result):
                    return result
                await asyncio.sleep(interval)
    except TimeoutError:
        return None
