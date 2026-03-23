import asyncio
import logging

from gh_tt.commands import gh, git
from gh_tt.modules import configuration

logger = logging.getLogger(__name__)


class WorkonError(Exception):
    pass


async def workon_issue(issue: int | gh.Issue, config: configuration.TtConfig, *, assign: bool):
    logger.debug('workon_issue: issue=%s, assign=%s', issue, assign)

    _, is_safe_to_switch_branch = await asyncio.gather(git.fetch(), git.is_safe_to_switch_branch())
    if not is_safe_to_switch_branch:
        raise WorkonError(
            'You have uncommitted changes to tracked files. Please commit or stash them before running this command.'
        )

    match issue:
        case int():
            issue, repo, remote = await asyncio.gather(
                gh.get_issue(issue), gh.get_repo(), git.get_remote()
            )
            logger.debug('fetched issue=%s, repo=%s, remote=%s', issue.title, repo.name, remote)
        case gh.Issue():
            repo, remote = await asyncio.gather(gh.get_repo(), git.get_remote())
            logger.debug('fetched repo=%s, remote=%s', repo.name, remote)

    assert isinstance(issue, gh.Issue), 'Expected issue to be an Issue object after the fetch step'

    if issue.closed:
        raise RuntimeError(
            'Issue is closed. Working on closed issues is not supported. Please open a new issue in favor of reopening issues.'
        )

    dev_branch = await _create_or_reuse_branch(issue=issue, repo=repo, remote=remote)

    if assign:
        logger.debug('assigning issue and PR to @me')
        await asyncio.gather(
            gh.assign_issue(issue_number=issue.number, assignee='@me'),
            gh.assign_pr(dev_branch=dev_branch, assignee='@me'),
        )

    if (
        config.project.number is not None
        and config.project.owner is not None
        and config.workon.status is not None
    ):
        logger.debug(
            'updating project status: owner=%s, number=%s, status=%s',
            config.project.owner,
            config.project.number,
            config.workon.status,
        )
        project = await gh.get_project(
            project_owner=config.project.owner, project_number=config.project.number
        )
        project_item = await gh.add_item_to_project(
            project_number=project.number, project_owner=project.owner, item_url=str(issue.url)
        )
        await gh.update_project_item_status(
            project_id=project.identifier,
            project_number=project.number,
            project_owner=project.owner,
            item_id=project_item.identifier,
            status_value=config.workon.status,
        )
    else:
        logger.debug('skipping project status update (project config not fully set)')

    print(str(issue.url))


async def workon_title(
    issue_title: str, issue_body: str | None, config: configuration.TtConfig, *, assign: bool
):
    logger.debug('workon_title: title=%s, assign=%s', issue_title, assign)
    issue = await gh.create_issue(title=issue_title, body=issue_body)
    await workon_issue(issue=issue, assign=assign, config=config)


async def _create_or_reuse_branch(issue: gh.Issue, repo: gh.Repo, remote: str) -> str:
    existing_branch = await git.check_branch_exists(issue.number)
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
            dev_branch, is_pr_open = await asyncio.gather(
                git.switch_branch(branch_name), gh.is_pr_open(branch_name)
            )

            if not is_pr_open:
                raise RuntimeError(
                    f"Found local branch '{dev_branch}', but could not find a corresponding open pull request. This indicates this branch was not created via `gh tt workon`. gh-tt currently does not support working on branches not created via gh-tt.\n\nTo fix this, please create a PR manually.\n\nIf this branch was created via gh tt workon, please report this as a bug."
                )

        case git.CheckBranchExistsResult(branch_type='remote', name=branch_name):
            logger.debug('found remote branch: %s', branch_name)
            dev_branch, is_pr_open = await asyncio.gather(
                git.switch_branch(
                    git.SwitchRemoteInput(branch_to_switch_to=branch_name, remote=remote)
                ),
                gh.is_pr_open(branch_name),
            )

            if not is_pr_open:
                raise RuntimeError(
                    f"Found remote branch '{dev_branch}', but could not find a corresponding open pull request. This indicates this branch was not created via `gh tt workon`. gh-tt currently does not support working on branches not created via gh-tt.\n\nTo fix this, please create a PR manually.\n\nIf this branch was created via gh tt workon, please report this as a bug."
                )

    return dev_branch
