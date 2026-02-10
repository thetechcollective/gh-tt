import asyncio
import contextlib
import logging

from gh_tt.classes.config import Config
from gh_tt.commands import gh, git

logger = logging.getLogger(__name__)


async def workon_issue(issue_number: int, *, assign: bool):
    logger.debug('workon_issue: issue_number=%d, assign=%s', issue_number, assign)
    config = Config().config()

    await git.fetch()
    issue, repo, remote = await asyncio.gather(
        gh.get_issue(issue_number), gh.get_repo(), git.get_remote()
    )
    logger.debug('fetched issue=%s, repo=%s, remote=%s', issue.title, repo.name, remote)

    if issue.closed:
        raise RuntimeError(
            'Issue is closed. Working on closed issues is not supported. Please open a new issue in favor of reopening issues.'
        )

    existing_branch = await git.check_branch_exists(issue_number)
    logger.debug('existing branch check result: %s', existing_branch)

    match existing_branch:
        case None:
            logger.debug('no existing branch, creating new dev branch')
            dev_branch = await gh.develop_issue(
                issue_title=issue.title,
                issue_number=issue.number,
                default_branch=repo.default_branch,
            )
            await git.push_empty_commit(dev_branch=dev_branch)
            await gh.create_draft_pr(
                issue_number=issue.number,
                issue_title=issue.title,
                default_branch=repo.default_branch,
            )
        case git.CheckBranchExistsResult(branch_type='local', name=branch_name):
            logger.debug('found local branch: %s', branch_name)
            dev_branch = await git.switch_branch(branch_name)
        case git.CheckBranchExistsResult(branch_type='remote', name=branch_name):
            logger.debug('found remote branch: %s', branch_name)
            dev_branch = await git.switch_branch(
                git.SwitchRemoteInput(branch_to_switch_to=branch_name, remote=remote)
            )
    if assign:
        logger.debug('assigning issue and PR to @me')
        await asyncio.gather(
            gh.assign_issue(issue_number=issue.number, assignee='@me'),
            gh.assign_pr(dev_branch=dev_branch, assignee='@me'),
        )

    project_owner = None
    project_number = None
    status_value = None
    with contextlib.suppress(KeyError):
        project_owner = config['project']['owner']
        project_number = config['project']['number']
        status_value = config['workon']['status']

    if project_number is not None and project_owner is not None and status_value is not None:
        logger.debug(
            'updating project status: owner=%s, number=%s, status=%s',
            project_owner,
            project_number,
            status_value,
        )
        project = await gh.get_project(project_owner=project_owner, project_number=project_number)
        project_item = await gh.add_item_to_project(
            project_number=project.number, project_owner=project.owner, item_url=str(issue.url)
        )
        await gh.update_project_item_status(
            project_id=project.identifier,
            project_number=project.number,
            project_owner=project.owner,
            item_id=project_item.identifier,
            status_value=status_value,
        )
    else:
        logger.debug('skipping project status update (project config not fully set)')


async def workon_title(issue_title: str, issue_body: str | None, *, assign: bool):
    logger.debug('workon_title: title=%s, assign=%s', issue_title, assign)
    issue = await gh.create_issue(title=issue_title, body=issue_body)
    await workon_issue(issue_number=issue.number, assign=assign)
