import asyncio
from dataclasses import dataclass
from typing import Literal

from async_lru import alru_cache

from gh_tt import shell


async def fetch():
    await shell.run(['git','fetch', '--tags', '--all'])

@alru_cache
async def get_remote() -> str:
    result = await shell.run(['git','remote'])
    return result.stdout

@alru_cache
async def get_local_branches() -> list[str]:
    result = await shell.run(['git','branch','--format=%(refname:short)'])

    return result.stdout.splitlines()

@alru_cache
async def get_remote_branches() -> list[str]:
    result = await shell.run(['git', 'branch', '-r', '--format=%(refname:short)'])

    return result.stdout.splitlines()

@dataclass
class CheckBranchExistsResult:
    branch_type: Literal['local', 'remote']
    name: str

async def check_branch_exists(issue_number: int) -> CheckBranchExistsResult | None:
    local_branches, remote_branches = await asyncio.gather(get_local_branches(), get_remote_branches())
    for b in local_branches:
        if b.startswith(f'{issue_number}-'):
            return CheckBranchExistsResult('local', name=b)
    
    for b in remote_branches:
        # Remote branches are prefixed with remote name (e.g., 'origin/1-branch-name')
        b = b.split('/', 1)[1] if '/' in b else b
        if b.startswith(f'{issue_number}-'):
            return CheckBranchExistsResult('remote', name=b)
        
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
            await shell.run(['git', 'switch', switch_input])
            return switch_input
        case SwitchRemoteInput(branch_to_switch_to=branch, remote=remote):
            await shell.run(['git', 'switch', '-c', branch, f'{remote}/{branch}'])
            return branch


async def push_empty_commit(dev_branch: str):
    await shell.run(['git', 'commit', '--allow-empty', '-m', 'PR start commit', '-m', 'This commit serves no other purpose than to allow creation of a PR when executing `gh tt workon`. Because creating a PR without a commit is not possible. This commit should be squashed or removed before merging this PR.'])
    await shell.run(['git', 'push', '-u', 'origin', dev_branch])

async def create_draft_pr(issue_number: int, issue_title: str, default_branch: str):
    # The PR would close the issue even without this reference, but mentioning the issue
    # is nice for quick access
    body = f'Closes #{issue_number}'
    title = f'Issue {issue_number}: {issue_title}'

    await shell.run(['gh', 'pr', 'create', '--base', default_branch, '--draft', '--title', title, '--body', body])

async def assign_pr(dev_branch: str, assignee: str):
    await shell.run(['gh', 'pr', 'edit', dev_branch, '--add-assignee', assignee])