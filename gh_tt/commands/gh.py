"""
Contains functions that execute command-line GitHub commands
"""

import json
import re
from typing import Literal

from async_lru import alru_cache
from pydantic import AliasPath, BaseModel, Field, HttpUrl, PositiveInt

from gh_tt import shell


async def create_draft_pr(issue_number: int, issue_title: str, default_branch: str):
    # The PR would close the issue even without this reference, but mentioning the issue
    # is nice for quick access
    body = f'Closes #{issue_number}'
    title = f'Issue {issue_number}: {issue_title}'

    await shell.run(
        [
            'gh',
            'pr',
            'create',
            '--base',
            default_branch,
            '--draft',
            '--title',
            title,
            '--body',
            body,
        ]
    )


async def assign_pr(dev_branch: str, assignee: str):
    await shell.run(['gh', 'pr', 'edit', dev_branch, '--add-assignee', assignee])


async def merge_pr(dev_branch: str):
    await shell.run(['gh', 'pr', 'merge', dev_branch, '--auto', '--squash', '--delete-branch'])


async def mark_pr_ready(dev_branch: str):
    await shell.run(['gh', 'pr', 'ready', dev_branch])


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

    await shell.run(
        cmd=[
            'gh',
            'issue',
            'develop',
            str(issue_number),
            '--base',
            default_branch,
            '--name',
            branch_name,
            '--checkout',
        ]
    )

    return branch_name


@alru_cache
async def get_issue(issue_number: int) -> Issue:
    result = await shell.run(
        cmd=[
            'gh',
            'issue',
            'view',
            str(issue_number),
            '--json',
            'url,title,number,labels,assignees,closed',
        ]
    )

    return Issue(**json.loads(result.stdout))


class Repo(BaseModel):
    name: str = Field(alias='nameWithOwner')
    default_branch: str = Field(alias=AliasPath('defaultBranchRef', 'name'))


@alru_cache
async def get_repo() -> Repo:
    result = await shell.run(['gh', 'repo', 'view', '--json', 'nameWithOwner,defaultBranchRef'])

    return Repo(**json.loads(result.stdout))


class Project(BaseModel):
    identifier: str = Field(alias='id')
    url: HttpUrl
    title: str
    number: int
    owner: str = Field(alias=AliasPath('owner', 'login'))


@alru_cache
async def get_project(project_number: int, project_owner: str) -> Project:
    result = await shell.run(
        ['gh', 'project', 'view', str(project_number), '--owner', project_owner, '--format', 'json']
    )

    return Project(**json.loads(result.stdout))


class ProjectItem(BaseModel):
    identifier: str = Field(alias='id')


async def add_item_to_project(
    project_number: int, project_owner: str, item_url: str
) -> ProjectItem:
    result = await shell.run(
        [
            'gh',
            'project',
            'item-add',
            str(project_number),
            '--owner',
            project_owner,
            '--url',
            item_url,
            '--format',
            'json',
        ]
    )

    return ProjectItem(**json.loads(result.stdout))


class StatusFieldOption(BaseModel):
    option_id: str = Field(alias='id')
    name: str


class ProjectStatusField(BaseModel):
    field_id: str = Field(alias='id')
    name: str
    type: Literal['ProjectV2SingleSelectField']
    options: list[StatusFieldOption]


async def update_project_item_status(
    project_id: str, project_number: int, project_owner: str, item_id: str, status_value: str
):
    status_field_name = 'Status'

    result = await shell.run(
        [
            'gh',
            'project',
            'field-list',
            str(project_number),
            '--owner',
            project_owner,
            '--format',
            'json',
            '--jq',
            f'.fields[] | select(.name == "{status_field_name}")',
        ]
    )

    project_status_field = ProjectStatusField(**json.loads(result.stdout))

    status_option_id = next(
        option.option_id for option in project_status_field.options if option.name == status_value
    )
    assert status_value, (
        f"Provided status value {status_value} is not among the options for the project's status field. Options: {[option.name for option in project_status_field.options]}"
    )

    await shell.run(
        [
            'gh',
            'project',
            'item-edit',
            '--project-id',
            project_id,
            '--field-id',
            project_status_field.field_id,
            '--id',
            item_id,
            '--single-select-option-id',
            status_option_id,
        ]
    )
