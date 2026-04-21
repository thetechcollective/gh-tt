#!/usr/bin/env python3

import asyncio
import logging
import sys

from gh_tt import configuration
from gh_tt.commands import git
from gh_tt.deliver import DeliverError, deliver
from gh_tt.legacy.semver import (
    BumpError,
    ReleaseType,
    Semver,
    handle_semver_bump,
    validate_bump_context,
)
from gh_tt.self_commands import upgrade
from gh_tt.workon import WorkonError, workon_issue, workon_title

logger = logging.getLogger(__name__)


def _abort_on_legacy_path(args):
    print(
        'This feature is no longer supported. Refer to the README on github.com/thetechcollective/gh-tt for supported features.',
        file=sys.stderr,
    )
    print(f'Passed arguments: {args}')
    sys.exit(1)


def handle_self(args):
    if args.self_command == 'upgrade':
        asyncio.run(upgrade(pin=args.pin))


def handle_workon(args):
    """Handle the workon command"""
    if args.pr_workflow:
        git_root = asyncio.run(git.get_root())
        config = configuration.load_config(git_root)

        try:
            if args.title:
                logger.debug('handle_workon: pr_workflow with title=%s', args.title)
                asyncio.run(
                    workon_title(
                        issue_title=args.title,
                        issue_body=args.body,
                        assign=args.assignee,
                        config=config,
                    )
                )
            else:
                logger.debug('handle_workon: pr_workflow with issue=%s', args.issue)
                asyncio.run(workon_issue(args.issue, assign=args.assignee, config=config))
        except WorkonError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        return

    _abort_on_legacy_path(args)


def _resolve_poll_flag(args) -> bool:
    """Resolve the poll flag: CLI > config > False."""
    if args.poll is not None:
        return args.poll

    git_root = asyncio.run(git.get_root())
    config = configuration.load_config(git_root)
    return config.deliver.policies.poll


def handle_deliver(args):
    """Handle the deliver command"""
    if args.pr_workflow:
        poll = _resolve_poll_flag(args)
        logger.debug(
            'handle_deliver: pr_workflow with delete_branch=%s, poll=%s', args.delete_branch, poll
        )
        try:
            asyncio.run(deliver(delete_branch=args.delete_branch, poll=poll))
        except DeliverError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return

    _abort_on_legacy_path(args)


def handle_semver(args):
    """Handle the semver command"""
    semver = Semver.with_tags_loaded()
    # Use the level to determine if this is a prerelease operation
    release_type = (
        ReleaseType.PRERELEASE
        if args.semver_command == 'bump' and args.level == 'prerelease'
        else ReleaseType.RELEASE
    )

    if args.semver_command == 'bump':
        try:
            asyncio.run(validate_bump_context())
        except BumpError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        handle_semver_bump(args, semver, release_type)
    elif args.semver_command == 'list':
        filter_type = getattr(args, 'filter_type', 'release')
        semver.list(release_type=release_type, filter_type=filter_type, show_sha=args.sha)
    elif args.semver_command is None:
        # Use the --prerelease flag directly from args when no subcommand is specified
        display_release_type = ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE
        current_semver = semver.get_current_semver(release_type=display_release_type)
        print(f'{current_semver}')


# Command handler mapping - exported for use by main
COMMAND_HANDLERS = {
    'workon': handle_workon,
    'deliver': handle_deliver,
    'semver': handle_semver,
}
