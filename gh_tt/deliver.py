import asyncio
import logging
import sys
from datetime import UTC, datetime

from rich.console import Console
from rich.live import Live
from rich.text import Text

from gh_tt.commands import gh, git
from gh_tt.commands.gh import TERMINAL_BUCKETS, CheckBucket
from gh_tt.shell import ShellError

logger = logging.getLogger(__name__)


class DeliverError(Exception):
    pass


def _format_check_line(check: gh.Check) -> str:
    match check.bucket:
        case CheckBucket.FAIL:
            return f'  ❌ {check.name} ({check.workflow}) — {check.link}'
        case CheckBucket.PASS:
            return f'  ✅ {check.name} ({check.workflow})'
        case CheckBucket.SKIPPING:
            return f'  ⏭️ {check.name} ({check.workflow})'
        case CheckBucket.PENDING:
            return f'  🔄 {check.name} ({check.workflow})'
        case _:
            raise AssertionError(f'Unexpected check bucket: {check.bucket}')


def _sort_checks(checks: list[gh.Check]) -> list[gh.Check]:
    order = {
        CheckBucket.PASS: 0,
        CheckBucket.SKIPPING: 1,
        CheckBucket.FAIL: 2,
        CheckBucket.PENDING: 3,
    }
    return sorted(checks, key=lambda c: order[c.bucket])


def _render_status(checks: list[gh.Check]) -> Text:
    now = datetime.now(tz=UTC).astimezone()
    timestamp = now.strftime('%H:%M:%S')
    terminal = [c for c in checks if c.bucket in TERMINAL_BUCKETS]
    total = len(checks)

    lines = [f'[{timestamp}] ⏳ {len(terminal)}/{total} checks completed']
    lines.extend(_format_check_line(check) for check in _sort_checks(checks))
    return Text('\n'.join(lines))


def _render_final(checks: list[gh.Check]) -> Text:
    now = datetime.now(tz=UTC).astimezone()
    timestamp = now.strftime('%H:%M:%S')
    total = len(checks)
    failed = [c for c in checks if c.bucket == CheckBucket.FAIL]

    if failed:
        header = f'[{timestamp}] ❌ {len(failed)}/{total} checks failed'
    else:
        header = f'[{timestamp}] ✅ All {total} checks passed'

    lines = [header]
    lines.extend(_format_check_line(check) for check in _sort_checks(checks))
    return Text('\n'.join(lines))


FIFTEEN_MINUTES_IN_SECONDS = 15 * 60


async def poll_checks(
    branch: str,
    *,
    interval_seconds: int = 5,
    timeout_seconds: int = FIFTEEN_MINUTES_IN_SECONDS,
    no_checks_retries: int = 5,
) -> bool:
    """Poll PR checks until all are terminal. Returns True if all passed."""
    console = Console(stderr=True)
    empty_polls = 0
    with Live(Text(''), console=console, refresh_per_second=4) as live:
        try:
            async with asyncio.timeout(timeout_seconds):
                while True:
                    try:
                        checks = await gh.get_pr_checks(branch)
                    except ShellError as e:
                        raise DeliverError(e.stderr) from e

                    if not checks:
                        empty_polls += 1
                        if empty_polls > no_checks_retries:
                            live.update(Text('No checks found on the PR.'))
                            return True
                        await asyncio.sleep(1)
                        continue

                    pending = [c for c in checks if c.bucket not in TERMINAL_BUCKETS]

                    if not pending:
                        live.update(_render_final(checks))
                        return all(c.bucket != CheckBucket.FAIL for c in checks)

                    live.update(_render_status(checks))
                    await asyncio.sleep(interval_seconds)
        except TimeoutError:
            if checks:
                live.update(_render_status(checks))
            print('Polling timed out.', file=sys.stderr)
            return False
        except KeyboardInterrupt:
            failed = [c for c in checks if c.bucket == CheckBucket.FAIL]
            for c in failed:
                print(c.link, file=sys.stderr)
            return True


async def deliver(*, delete_branch: bool, poll: bool = False):
    logger.debug('deliver: delete_branch=%s, poll=%s', delete_branch, poll)
    current_branch, _, remote, default_branch = await asyncio.gather(
        git.get_current_branch_name(), git.fetch(), git.get_remote(), gh.get_default_branch()
    )
    logger.debug(
        'current branch: %s, remote: %s, default_branch: %s',
        current_branch,
        remote,
        default_branch,
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
        raise DeliverError(
            f'The {default_branch} branch has commits your branch does not. Run git rebase {remote}/{default_branch} to integrate commits from {default_branch}.'
        )

    if remote_dev_branch_tip_hash != current_branch_tip_hash:
        logger.debug(
            'branch %s is not up to date with its remote %s/%s',
            current_branch,
            remote,
            current_branch,
        )
        raise DeliverError(
            f'Branch {current_branch} is not up to date with its remote. You may have unpushed commits on your local branch. Align your local branch with its remote before delivering.'
        )

    logger.debug(
        'branch is up to date and commits are pushed, marking PR ready and fetching PR info'
    )
    pr, _ = await asyncio.gather(gh.get_pr(), gh.mark_pr_ready(dev_branch=current_branch))
    logger.debug('merging PR on branch %s', current_branch)
    await gh.merge_pr(dev_branch=current_branch, delete_branch=delete_branch)
    logger.debug('PR merged successfully: %s', pr.url)

    print(str(pr.url))

    if poll:
        passed = await poll_checks(current_branch)
        if not passed:
            sys.exit(1)
