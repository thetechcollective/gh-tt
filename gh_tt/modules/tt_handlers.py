#!/usr/bin/env python3

import contextlib
import sys

from gh_tt.classes import sync
from gh_tt.classes.config import Config
from gh_tt.classes.devbranch import Devbranch
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.issue import Issue
from gh_tt.classes.label import Label
from gh_tt.classes.semver import ExecutionMode, ReleaseType, Semver
from gh_tt.classes.status import Status


def handle_workon(args):
    """Handle the workon command"""
    devbranch = Devbranch()
    label = None

    if args.type is not None:
        Label.validate(args.type, "type")

    if args.issue:
        if label is None:
            with contextlib.suppress(KeyError, AttributeError):
                label = Config().config()['workon']['default_type_labels']['issue']

        devbranch.set_issue(issue_number=args.issue, assign=args.assignee, msg=args.body, reopen=args.reopen, label=label)
        
    elif args.title:
        if label is None:
            with contextlib.suppress(KeyError, AttributeError):
                label = Config().config()['workon']['default_type_labels']['title']
        issue = Issue.create_new(title=args.title, body=args.body)
        devbranch.set_issue(issue_number=issue.get('number'), assign=args.assignee, reopen=args.reopen, label=label)


def handle_wrapup(args):
    """Handle the wrapup command"""
    devbranch = Devbranch()
    message = args.message_by_flag or args.message  
    devbranch.wrapup(message)
    
    if args.poll is not None:
        if args.poll:
            Status.poll()

        return
    
    config_poll = False
    # If the config value is not set, proceed with False
    with contextlib.suppress(KeyError):
        config_poll = Config.config()['wrapup']['policies']['poll']

    if config_poll:
        Status.poll()


def handle_deliver(args):
    """Handle the deliver command"""
    devbranch = Devbranch()
    squeeze_sha = devbranch.deliver()
    
    if args.poll is not None:
        if args.poll:
            Status.poll(sha=squeeze_sha)

        return

    config_poll = False
    # If the config value is not set, proceed with False
    with contextlib.suppress(KeyError):
        config_poll = Config.config()['deliver']['policies']['poll']

    if config_poll:
        Status.poll(sha=squeeze_sha)

def handle_responsibles(args):
    """Handle the responsibles command"""
    devbranch = Devbranch()
    devbranch.responsibles(unstaged=args.unstaged, staged=args.staged, exclude=args.exclude)


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
    
    cmd = f"git tag -a -m \"{tag_str}\n{message}\" {tag_str}"
    
    if args.run:
        import asyncio
        asyncio.run(Gitter(cmd=cmd, msg=message).run())
    else:
        print(cmd)


def _handle_semver_bump(args, semver, release_type):
    """Handle the semver bump subcommand"""
    assert args.level in ['major', 'minor', 'patch', 'prerelease', 'build']

    # For build level, we need to use the bump_build method directly
    if args.level == 'build':
        _handle_semver_bump_build(args, semver)
    else:
        semver.bump(
            level=args.level, 
            message=args.message, 
            prefix=args.prefix, 
            release_type=release_type,
            execution_mode=ExecutionMode.LIVE if args.run else ExecutionMode.DRY_RUN
        )


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
    elif args.semver_command == 'note':
        if args.filename:
            note = semver.note(release_type=release_type, filename=args.filename, from_ref=args.from_ref, to_ref=args.to_ref)
            print(f"{args.filename}")
        else:
            note = semver.note(release_type=release_type, from_ref=args.from_ref, to_ref=args.to_ref)
            print(note)
    elif args.semver_command is None:
        # Use the --prerelease flag directly from args when no subcommand is specified
        display_release_type = ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE
        current_semver = semver.get_current_semver(release_type=display_release_type)
        print(f"{current_semver}")


def handle_status(args):
    """Handle the status command"""
    if args.status_command == 'get':
         Status.poll(sha=args.sha)
    elif args.status_command == 'set':
        Status.set_status_sync(
            state=args.state, 
            description=args.description, 
            context=args.context, 
            target_url=args.target_url, 
            sha=args.sha
        )

def handle_sync(args):
    assert args.labels or args.milestones
    
    sync.sync(labels=args.labels, milestones=args.milestones)

# Command handler mapping - exported for use by main
COMMAND_HANDLERS = {
    'workon': handle_workon,
    'wrapup': handle_wrapup,
    'deliver': handle_deliver,
    'responsibles': handle_responsibles,
    'semver': handle_semver,
    'status': handle_status,
    'sync': handle_sync,
}
