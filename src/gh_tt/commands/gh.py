"""
Contains functions that execute command-line GitHub commands
"""

import json
import logging
import re
from enum import Enum
from typing import Literal

from async_lru import alru_cache
from pydantic import AliasPath, BaseModel, Field, HttpUrl, PositiveInt

from gh_tt import shell

logger = logging.getLogger(__name__)


@alru_cache
async def get_default_branch() -> str:
    result = await shell.run(
        ['gh', 'repo', 'view', '--json', 'defaultBranchRef', '--jq', '.defaultBranchRef.name']
    )

    return result.stdout


class PullRequestState(Enum):
    Open = 'OPEN'
    Closed = 'CLOSED'
    Merged = 'MERGED'


class Commit(BaseModel):
    message_headline: str = Field(alias='messageHeadline')
    message_body: str = Field(alias='messageBody')


class PullRequest(BaseModel):
    url: HttpUrl
    state: PullRequestState
    body: str
    commits: list[Commit]


async def get_pr() -> PullRequest:
    result = await shell.run(['gh', 'pr', 'view', '--json', 'url,state,body,commits'])

    return PullRequest(**json.loads(result.stdout))


async def create_draft_pr(issue_number: int, issue_title: str, default_branch: str):
    logger.debug('creating draft PR for issue #%d on base %s', issue_number, default_branch)
    # The PR would close the issue even without this reference, but mentioning the issue
    # is nice for quick access
    body = f'Closes #{issue_number}'
    title = f'Issue #{issue_number}: {issue_title}'

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


class CheckBucket(Enum):
    PENDING = 'pending'
    PASS = 'pass'  # noqa: S105
    FAIL = 'fail'
    SKIPPING = 'skipping'


TERMINAL_BUCKETS = frozenset({CheckBucket.PASS, CheckBucket.FAIL, CheckBucket.SKIPPING})


class Check(BaseModel):
    name: str
    bucket: CheckBucket
    workflow: str
    link: HttpUrl


async def get_pr_checks(branch: str) -> list[Check]:
    """Fetch the current check runs for the PR corresponding to the input branch."""
    result = await shell.run(
        ['gh', 'pr', 'checks', branch, '--json', 'name,state,bucket,workflow,link'],
        die_on_error=False,
    )

    if result.return_code != 0:
        # This can mean that GitHub has not 'loaded' the checks
        # that are supposed to run on the PR. So return empty array
        # because we can 'recover' by retrying the call.
        if 'no checks reported on the' in result.stderr:
            return []
        raise shell.ShellError(
            cmd=['gh', 'pr', 'checks'],
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.return_code,
        )

    return [Check(**item) for item in json.loads(result.stdout)]


async def merge_pr(dev_branch: str, *, delete_branch: bool, body: str):
    logger.debug('merging PR on branch %s (delete_branch=%s)', dev_branch, delete_branch)
    cmd = ['gh', 'pr', 'merge', dev_branch, '--auto', '--squash', '--body', body]
    if delete_branch:
        cmd.append('--delete-branch')

    await shell.run(cmd)


async def mark_pr_ready(dev_branch: str):
    await shell.run(['gh', 'pr', 'ready', dev_branch])


async def is_pr_open(dev_branch: str) -> bool:
    result = await shell.run(
        ['gh', 'pr', 'view', dev_branch, '--json', 'url,state,body,commits'], die_on_error=False
    )

    if result.return_code == 1:
        # Did not find PR
        return False

    pr = PullRequest(**json.loads(result.stdout))
    return pr.state is PullRequestState.Open


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
    logger.debug('developing issue #%d with branch %s', issue_number, branch_name)

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


async def create_issue(title: str, body: str | None = None) -> Issue:
    logger.debug('creating issue: %s', title)
    result = await shell.run(
        cmd=['gh', 'issue', 'create', '--title', title, '--body', body if body is not None else '']
    )

    # Command above outputs the issue URL, e.g.
    # https://github.com/thetechcollective/gh-tt/issues/462
    issue_number = int(result.stdout.split('/')[-1])

    issue_view_cmd = [
        'gh',
        'issue',
        'view',
        str(issue_number),
        '--json',
        'url,title,number,labels,assignees,closed',
    ]

    # GitHub API has eventual consistency — the issue may not be queryable immediately after creation
    issue_result = await shell.poll_until(
        cmd=issue_view_cmd,
        predicate=lambda r: bool(r.stdout),
        timeout_seconds=15,
        interval=1,
    )

    if issue_result is None:
        raise shell.ShellError(
            cmd=issue_view_cmd,
            stdout='',
            stderr=f'Timed out waiting for issue #{issue_number} to become available',
            return_code=1,
        )

    return Issue(**json.loads(issue_result.stdout))


class Repo(BaseModel):
    name: str = Field(alias='nameWithOwner')
    default_branch: str = Field(validation_alias=AliasPath('defaultBranchRef', 'name'))


@alru_cache
async def get_repo() -> Repo:
    result = await shell.run(['gh', 'repo', 'view', '--json', 'nameWithOwner,defaultBranchRef'])

    return Repo(**json.loads(result.stdout))


class Project(BaseModel):
    identifier: str = Field(alias='id')
    url: HttpUrl
    title: str
    number: int
    owner: str = Field(validation_alias=AliasPath('owner', 'login'))


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
    logger.debug('updating project item status: item=%s, status=%s', item_id, status_value)
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


async def get_gh_cli_version() -> str:
    """Returns the version of the GH CLI in a semver style, e.g. 2.88.1"""

    result = await shell.run(['gh', '--version'])
    version = result.stdout.split()[2]

    assert version.count('.') == 2
    assert len(version.split('.')) == 3

    return version


async def get_gh_auth_scopes() -> list[str]:
    """Returns the scopes the gh cli is authenticated for"""

    result = await shell.run(['gh', 'auth', 'status', '--json', 'hosts'])
    raw = result.stdout
    parsed = json.loads(raw)

    # Assume one authenticated instance for github it is proven we
    # need to be smarter about this
    first_host = parsed['hosts']['github.com'][0]

    assert 'github.com' in parsed['hosts']
    assert first_host['active'] is True
    assert 'scopes' in first_host

    return first_host['scopes'].split(', ')
