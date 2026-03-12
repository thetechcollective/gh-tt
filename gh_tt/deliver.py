import asyncio
import logging
import sys

from gh_tt.commands import gh, git

logger = logging.getLogger(__name__)


async def deliver(*, delete_branch: bool):
    logger.debug('deliver: delete_branch=%s', delete_branch)
    dev_branch, _, remote, default_branch = await asyncio.gather(
        git.get_current_branch_name(), git.fetch(), git.get_remote(), gh.get_default_branch()
    )
    logger.debug(
        'current branch: %s, remote: %s, default_branch: %s', dev_branch, remote, default_branch
    )

    default_head_hash, merge_base_hash = await asyncio.gather(
        git.get_default_head_hash(remote=remote, default_branch=default_branch),
        git.get_merge_base(branch=dev_branch, remote=remote, default_branch=default_branch),
    )
    logger.debug('default_head_hash=%s, merge_base_hash=%s', default_head_hash, merge_base_hash)

    if default_head_hash != merge_base_hash:
        logger.debug('branch %s is not up to date with %s/%s', dev_branch, remote, default_branch)
        print(
            f'The {default_branch} has commits your branch does not. Run git rebase {remote}/{default_branch} to integrate commits from {default_branch}.',
            file=sys.stderr,
        )
        sys.exit(1)

    logger.debug('branch is up to date, marking PR ready and fetching PR info')
    pr, _ = await asyncio.gather(gh.get_pr(), gh.mark_pr_ready(dev_branch=dev_branch))
    logger.debug('merging PR on branch %s', dev_branch)
    await gh.merge_pr(dev_branch=dev_branch, delete_branch=delete_branch)
    logger.debug('PR merged successfully: %s', pr.url)

    print(str(pr.url))
