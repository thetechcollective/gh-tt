#!/usr/bin/env python3

import contextlib

from gh_tt.classes.config import Config
from gh_tt.classes.devbranch import Devbranch
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
    if args.poll:
        Status.poll()


def handle_deliver(_args):
    """Handle the deliver command"""
    devbranch = Devbranch()
    devbranch.deliver()


def handle_responsibles(args):
    """Handle the responsibles command"""
    devbranch = Devbranch()
    devbranch.responsibles(unstaged=args.unstaged, staged=args.staged, exclude=args.exclude)


def handle_semver(args):
    """Handle the semver command"""
    semver = Semver()
    
    if args.semver_command == 'bump':
        semver.bump(
            level=args.level, 
            message=args.message, 
            suffix=args.suffix, 
            prefix=args.prefix, 
            initial=args.initial, 
            release_type=ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE, 
            execution_mode=ExecutionMode.LIVE if args.run else ExecutionMode.DRY_RUN
        )
    elif args.semver_command == 'list':
        semver.list(release_type=ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE)
    elif args.semver_command == 'note':
        if args.filename:
            note = semver.note(prerelease=ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE, filename=args.filename)
            print(f"{args.filename}")
        else:
            note = semver.note(prerelease=ReleaseType.PRERELEASE if args.prerelease else ReleaseType.RELEASE)
            print(note)
    elif args.semver_command is None:
        current_semver = semver.get_current_semver(release_type=args.prerelease)
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



# Command handler mapping - exported for use by main
COMMAND_HANDLERS = {
    'workon': handle_workon,
    'wrapup': handle_wrapup,
    'deliver': handle_deliver,
    'responsibles': handle_responsibles,
    'semver': handle_semver,
    'status': handle_status,
}
