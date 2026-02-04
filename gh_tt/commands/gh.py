"""
Contains functions that execute command-line GitHub commands
"""


import json
import re

from async_lru import alru_cache
from pydantic import AliasPath, BaseModel, Field, HttpUrl, PositiveInt

from gh_tt import shell


async def create_draft_pr(issue_number: int, issue_title: str, default_branch: str):
    # The PR would close the issue even without this reference, but mentioning the issue
    # is nice for quick access
    body = f'Closes #{issue_number}'
    title = f'Issue {issue_number}: {issue_title}'

    await shell.run(['gh', 'pr', 'create', '--base', default_branch, '--draft', '--title', title, '--body', body])


async def assign_pr(dev_branch: str, assignee: str):
    await shell.run(['gh', 'pr', 'edit', dev_branch, '--add-assignee', assignee])


class Label(BaseModel):
    identifier: str = Field(alias='id', pattern=r'^LA')
    name: str
    description: str = Field(max_length=100)
    color: str = Field(min_length=6, max_length=6)

class Assignee(BaseModel):
    identifier: str = Field(alias='id')
    name: str
    login: str

class Issue(BaseModel):
    url: HttpUrl
    title: str
    number: PositiveInt
    labels: list[Label]
    assignees: list[Assignee]
    closed: bool

async def assign_issue(issue_number: int, assignee: str):
    await shell.run(cmd=['gh', 'issue', 'edit', str(issue_number), '--add-assignee', assignee])


async def develop_issue(issue_title: str, issue_number: int, default_branch: str) -> str:
    sanitized_title = re.sub(r'[^a-zA-Z0-9]+', '_', issue_title)
    branch_name = f'{issue_number}-{sanitized_title}'

    await shell.run(cmd=['gh', 'issue', 'develop', str(issue_number), '--base', default_branch, '--name', branch_name, '--checkout'])

    return branch_name


@alru_cache
async def get_issue(issue_number: int) -> Issue:
    result = await shell.run(cmd=['gh', 'issue', 'view', str(issue_number), '--json', 'url,title,number,labels,assignees,closed'])

    return Issue(**json.loads(result.stdout))

class Repo(BaseModel):
    name: str = Field(alias='nameWithOwner')
    default_branch: str = Field(alias=AliasPath('defaultBranchRef', 'name'))

@alru_cache
async def get_repo() -> Repo:
    result = await shell.run(['gh', 'repo', 'view', '--json', 'nameWithOwner,defaultBranchRef'])
    
    return Repo(**json.loads(result.stdout))