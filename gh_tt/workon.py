import asyncio

from gh_tt.commands import gh, git


async def workon_issue(issue_number: int, *, assign: bool):
    await git.fetch()
    issue, repo, remote = await asyncio.gather(gh.get_issue(issue_number), gh.get_repo(), git.get_remote())

    if issue.closed:
        raise RuntimeError(
            "Issue is closed. Working on closed issues is not supported. Please open a new issue in favor of reopening issues."
        )

    existing_branch = await git.check_branch_exists(issue_number)

    match existing_branch:
        case None:
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
        case git.CheckBranchExistsResult(branch_type="local", name=branch_name):
            dev_branch = await git.switch_branch(branch_name)
        case git.CheckBranchExistsResult(branch_type="remote", name=branch_name):
            dev_branch = await git.switch_branch(git.SwitchRemoteInput(branch_to_switch_to=branch_name, remote=remote))
    if assign:
        await asyncio.gather(
            gh.assign_issue(issue_number=issue.number, assignee="@me"),
            gh.assign_pr(dev_branch=dev_branch, assignee="@me"),
        )

    # add to project