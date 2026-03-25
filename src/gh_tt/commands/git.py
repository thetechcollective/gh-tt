"""
Contains functions that execute command-line git commands
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from async_lru import alru_cache

from gh_tt import shell

logger = logging.getLogger(__name__)


async def get_root() -> Path:
    result = await shell.run(['git', 'rev-parse', '--show-toplevel'])
    return Path(result.stdout)


async def is_safe_to_switch_branch() -> bool:
    result = await shell.run(['git', 'status', '--porcelain'])

    # ?? marks untracked files - we can safely switch branches with those
    return all(line.startswith('??') for line in result.stdout.splitlines())


async def fetch():
    await shell.run(['git', 'fetch', '--tags', '--all'])


@alru_cache
async def get_remote() -> str:
    result = await shell.run(['git', 'remote'])
    assert '\n' not in result.stdout, f'Multiple remotes are not supported, found: {result.stdout}'
    return result.stdout


@alru_cache
async def get_local_branches() -> list[str]:
    result = await shell.run(['git', 'branch', '--format=%(refname:short)'])

    return result.stdout.splitlines()


@alru_cache
async def get_remote_branches() -> list[str]:
    result = await shell.run(['git', 'branch', '-r', '--format=%(refname:short)'])

    return result.stdout.splitlines()


async def get_current_branch_name() -> str:
    result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    return result.stdout


async def get_branch_tip_hash(branch: str, remote: str | None = None) -> str:
    ref = f'{remote}/{branch}' if remote else branch
    result = await shell.run(['git', 'rev-parse', ref])
    return result.stdout


async def get_merge_base(branch: str, remote: str, default_branch: str) -> str:
    result = await shell.run(['git', 'merge-base', branch, f'{remote}/{default_branch}'])
    return result.stdout


@dataclass
class CheckBranchExistsResult:
    branch_type: Literal['local', 'remote']
    name: str


async def check_branch_exists(issue_number: int) -> CheckBranchExistsResult | None:
    logger.debug('checking if branch exists for issue #%d', issue_number)
    local_branches, remote_branches = await asyncio.gather(
        get_local_branches(), get_remote_branches()
    )
    for b in local_branches:
        if b.startswith(f'{issue_number}-'):
            logger.debug('found local branch: %s', b)
            return CheckBranchExistsResult('local', name=b)

    for b in remote_branches:
        # Remote branches are prefixed with remote name (e.g., 'origin/1-branch-name')
        b = b.split('/', 1)[1] if '/' in b else b
        if b.startswith(f'{issue_number}-'):
            logger.debug('found remote branch: %s', b)
            return CheckBranchExistsResult('remote', name=b)

    logger.debug('no branch found for issue #%d', issue_number)
    return None


@dataclass
class SwitchRemoteInput:
    branch_to_switch_to: str
    remote: str


type LocalBranchName = str
type BranchName = str


async def switch_branch(switch_input: LocalBranchName | SwitchRemoteInput) -> BranchName:
    match switch_input:
        case str():
            logger.debug('switching to local branch: %s', switch_input)
            await shell.run(['git', 'switch', switch_input])
            return switch_input
        case SwitchRemoteInput(branch_to_switch_to=branch, remote=remote):
            logger.debug('switching to remote branch: %s/%s', remote, branch)
            await shell.run(['git', 'switch', '-c', branch, f'{remote}/{branch}'])
            return branch


async def push_empty_commit(dev_branch: str):
    logger.debug('pushing empty commit on branch %s', dev_branch)
    status = await shell.run(['git', 'status', '--porcelain'])
    has_changes = bool(status.stdout)

    if has_changes:
        logger.debug('stashing existing changes before empty commit')
        await shell.run(['git', 'stash', '--include-untracked'])

    try:
        await shell.run(
            [
                'git',
                'commit',
                '--allow-empty',
                '--no-verify',
                '-m',
                'PR start commit',
                '-m',
                'This commit serves no other purpose than to allow creation of a PR when executing `gh tt workon`. Because creating a PR without a commit is not possible. This commit should be squashed or removed before merging this PR.',
            ]
        )
        await shell.run(['git', 'push', '-u', 'origin', dev_branch])
    finally:
        if has_changes:
            logger.debug('restoring stashed changes')
            await shell.run(['git', 'stash', 'pop'])
