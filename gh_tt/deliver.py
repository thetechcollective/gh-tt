import asyncio
import logging

from gh_tt.commands import gh, git

logger = logging.getLogger(__name__)


async def deliver(*, delete_branch: bool):
    logger.debug('deliver: delete_branch=%s', delete_branch)
    dev_branch = await git.get_current_branch()
    logger.debug('current branch: %s', dev_branch)

    pr, _ = await asyncio.gather(gh.get_pr(), gh.mark_pr_ready(dev_branch=dev_branch))
    await gh.merge_pr(dev_branch=dev_branch, delete_branch=delete_branch)

    print(str(pr.url))
