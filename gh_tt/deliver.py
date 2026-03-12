import asyncio
import logging
import sys

from gh_tt.commands import gh, git

logger = logging.getLogger(__name__)


async def deliver(*, delete_branch: bool):
    logger.debug('deliver: delete_branch=%s', delete_branch)
    current_branch, _, remote, default_branch = await asyncio.gather(
        git.get_current_branch_name(), git.fetch(), git.get_remote(), gh.get_default_branch()
    )
    logger.debug(
        'current branch: %s, remote: %s, default_branch: %s', current_branch, remote, default_branch
    )

    (
        default_branch_tip_hash,
        remote_dev_branch_tip_hash,
        current_branch_tip_hash,
        merge_base_hash,
    ) = await asyncio.gather(
        git.get_branch_tip_hash(remote=remote, branch=default_branch),
        git.get_branch_tip_hash(remote=remote, branch=current_branch),
        git.get_branch_tip_hash(branch='HEAD'),
        git.get_merge_base(branch=current_branch, remote=remote, default_branch=default_branch),
    )
    logger.debug(
        'default_branch_tip_hash=%s, remote_dev_branch_tip_hash=%s, current_branch_tip_hash=%s merge_base_hash=%s',
        default_branch_tip_hash,
        remote_dev_branch_tip_hash,
        current_branch_tip_hash,
        merge_base_hash,
    )

    if default_branch_tip_hash != merge_base_hash:
        logger.debug(
            'branch %s is not up to date with %s/%s', current_branch, remote, default_branch
        )
        print(
            f'The {default_branch} branch has commits your branch does not. Run git rebase {remote}/{default_branch} to integrate commits from {default_branch}.',
            file=sys.stderr,
        )
        sys.exit(1)

    if remote_dev_branch_tip_hash != current_branch_tip_hash:
        logger.debug(
            'branch %s is not up to date with its remote %s/%s',
            current_branch,
            remote,
            current_branch,
        )
        print(
            f'Branch {current_branch} is not up to date with its remote. You may have unpushed commits on your local branch. Align your local branch with its remote before delivering.',
            file=sys.stderr,
        )
        sys.exit(1)

    logger.debug(
        'branch is up to date and commits are pushed, marking PR ready and fetching PR info'
    )
    pr, _ = await asyncio.gather(gh.get_pr(), gh.mark_pr_ready(dev_branch=current_branch))
    logger.debug('merging PR on branch %s', current_branch)
    await gh.merge_pr(dev_branch=current_branch, delete_branch=delete_branch)
    logger.debug('PR merged successfully: %s', pr.url)

    print(str(pr.url))
