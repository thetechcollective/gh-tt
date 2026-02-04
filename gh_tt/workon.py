import asyncio

from gh_tt.git import (
    CheckBranchExistsResult,
    SwitchRemoteInput,
    assign_pr,
    check_branch_exists,
    create_draft_pr,
    fetch,
    get_remote,
    push_empty_commit,
    switch_branch,
)
from gh_tt.issue import assign_issue, develop_issue, get_issue
from gh_tt.repo import get_repo


async def workon_issue(issue_number: int, *, assign: bool):
    await fetch()
    issue, repo, remote = await asyncio.gather(get_issue(issue_number), get_repo(), get_remote())

    if issue.closed:
        raise RuntimeError(
            "Issue is closed. Working on closed issues is not supported. Please open a new issue in favor of reopening issues."
        )

    existing_branch = await check_branch_exists(issue_number)

    match existing_branch:
        case None:
            dev_branch = await develop_issue(
                issue_title=issue.title,
                issue_number=issue.number,
                default_branch=repo.default_branch,
            )
            await push_empty_commit(dev_branch=dev_branch)
            await create_draft_pr(
                issue_number=issue.number,
                issue_title=issue.title,
                default_branch=repo.default_branch,
            )
        case CheckBranchExistsResult(branch_type="local", name=branch_name):
            dev_branch = await switch_branch(branch_name)
        case CheckBranchExistsResult(branch_type="remote", name=branch_name):
            dev_branch = await switch_branch(SwitchRemoteInput(branch_to_switch_to=branch_name, remote=remote))
    if assign:
        await asyncio.gather(
            assign_issue(issue_number=issue.number, assignee="@me"),
            assign_pr(dev_branch=dev_branch, assignee="@me"),
        )
