#!/usr/bin/env python3

import asyncio
import logging
import sys

from gh_tt import configuration, shell
from gh_tt.commands import git
from gh_tt.deliver import DeliverError, deliver
from gh_tt.legacy.semver import ExecutionMode, ReleaseType, Semver
from gh_tt.workon import workon_issue, workon_title

logger = logging.getLogger(__name__)

def _abort_on_legacy_path(args):
    print('This feature is no longer supported. Refer to the README on github.com/thetechcollective/gh-tt for supported features.', file=sys.stderr)
    print(f'Passed arguments: {args}')
    sys.exit(1)


def handle_workon(args):
    """Handle the workon command"""
    if args.pr_workflow:
        git_root = asyncio.run(git.get_root())
        config = configuration.load_config(git_root)

        if args.title:
            logger.debug("handle_workon: pr_workflow with title=%s", args.title)
            asyncio.run(workon_title(issue_title=args.title, issue_body=args.body, assign=args.assignee, config=config))
        else:
            logger.debug("handle_workon: pr_workflow with issue=%s", args.issue)
            asyncio.run(workon_issue(args.issue, assign=args.assignee, config=config))
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
        logger.debug("handle_deliver: pr_workflow with delete_branch=%s, poll=%s", args.delete_branch, poll)
        try:
            asyncio.run(deliver(delete_branch=args.delete_branch, poll=poll))
        except DeliverError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return

    _abort_on_legacy_path(args)


def _handle_semver_bump_build(args, semver):
    """Handle the semver bump build subcommand"""
    # First try to get a prerelease version, if not available fall back to release
    current_version = semver.get_current_semver(release_type=ReleaseType.PRERELEASE)
    if not current_version:
        current_version = semver.get_current_semver(release_type=ReleaseType.RELEASE)
    
    if not current_version:
        print("No version found to bump build number.", file=sys.stderr)
        sys.exit(1)
        
    new_version = current_version.version.bump_build(include_sha=args.include_sha)
    # Handle the prefix if specified
    tag_str = f"{args.prefix or ''}{new_version}"
    message = f"Bumped build from version '{current_version}' to '{tag_str}'"
    if args.message:
        message += f"\n{args.message}"
    
    cmd = ["git", "tag", "-a", "-m", f"{tag_str}\n{message}", tag_str]
    
    if args.run:
        asyncio.run(shell.run(cmd))
        # Print the new tag when in --run mode
        print(f"{tag_str}")
    else:
        print(" ".join(cmd))


def _handle_semver_bump(args, semver, release_type):
    """Handle the semver bump subcommand"""
    assert args.level in ['major', 'minor', 'patch', 'prerelease', 'build']

    # For build level, we need to use the bump_build method directly
    if args.level == 'build':
        _handle_semver_bump_build(args, semver)
    else:
        result = semver.bump(
            level=args.level, 
            message=args.message, 
            prefix=args.prefix, 
            release_type=release_type,
            execution_mode=ExecutionMode.LIVE if args.run else ExecutionMode.DRY_RUN
        )
        
        # Print the new tag in --run mode (which is the default)
        if args.run and result:
            # The result from bump() is a set with a single item - the new tag
            new_tag = next(iter(result))
            print(f"{new_tag}")


def handle_semver(args):
    """Handle the semver command"""
    semver = Semver.with_tags_loaded()
    # Use the level to determine if this is a prerelease operation
    release_type = ReleaseType.PRERELEASE if args.semver_command == 'bump' and args.level == 'prerelease' else ReleaseType.RELEASE
    
    if args.semver_command == 'bump':
        _handle_semver_bump(args, semver, release_type)
    elif args.semver_command == 'list':
        filter_type = getattr(args, 'filter_type', 'release')
        semver.list(release_type=release_type, filter_type=filter_type, show_sha=args.sha)
    elif args.semver_command is None:
        # Use the --prerelease flag directly from args when no subcommand is specified
        display_release_type = ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE
        current_semver = semver.get_current_semver(release_type=display_release_type)
        print(f"{current_semver}")


# Command handler mapping - exported for use by main
COMMAND_HANDLERS = {
    'workon': handle_workon,
    'deliver': handle_deliver,
    'semver': handle_semver,
}
