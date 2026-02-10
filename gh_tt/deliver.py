from gh_tt.commands import gh, git


async def deliver(*, delete_branch: bool):
    dev_branch = await git.get_current_branch()
    await gh.mark_pr_ready(dev_branch=dev_branch)
    await gh.merge_pr(dev_branch=dev_branch, delete_branch=delete_branch)
