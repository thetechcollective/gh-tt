#!/usr/bin/env python3

import argparse
import sys

from gh_tt.classes.config import Config
from gh_tt.classes.devbranch import Devbranch
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.issue import Issue
from gh_tt.classes.label import Label
from gh_tt.classes.semver import Semver


def parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output', default=False)

    version_parser = argparse.ArgumentParser(add_help=False)
    version_parser.add_argument('--version', action='store_true', help='Print version information and exit')

    prerelease_parser = argparse.ArgumentParser(add_help=False)
    prerelease_parser.add_argument('--prerelease', action='store_true', help='Set or read pre-release tags')
    
    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog='gh tt', 
        parents=[parent_parser, version_parser],
        description="""
            A command-line tool to support a consistent team workflow. 
            It supports a number of subcommands which define the entire process: `workon`,
            `wrapup`, `deliver`.  Use the `-h|--help` switch on each to learn more. The extension utilizes 
            the GitHub CLI tool `gh` to interact with GitHub and therefore it's provided as a gh extension. 
            GitHub Projects integration is supported. It enables issues to automatically 
            propagate through the columns in the (kanban) board. Please consult the README.md file 
            in 'thetechcollective/gh-tt' for more information on how to enable this feature 
            - and many more neat tricks.  
            """,)

    subparsers = parser.add_subparsers(dest='command')
    # Add workon subcommand
    workon_parser = subparsers.add_parser('workon', parents=[parent_parser], help='Set the issue number context to work on')
    workon_group = workon_parser.add_mutually_exclusive_group()
    workon_group.add_argument('-i', '--issue', type=int, help='Issue number')
    workon_group.add_argument('-t', '--title', type=str, help='Title for the new issue')
    workon_parser.add_argument('--type', type=str, help='Set an issue type label', default=None)
    workon_parser.add_argument('-b', '--body', dest='body', type=str, help='Optional body (issue comment) for the new issue')
    workon_parser.add_argument('-r', '--reopen', action='store_true', help='Reopens a closed issue. Required when you want to continue working on a closed issue.', default=False)
    assign_group = workon_parser.add_mutually_exclusive_group()
    assign_group.add_argument('--assign', dest='assignee', action='store_true', help='Assign @me to the issue (default)')
    assign_group.add_argument('--no-assign', dest='assignee', action='store_false', help='Do not assign anybody to the issue')
    workon_parser.set_defaults(assignee=True, exclusive_groups=['workon'])
    
    # Add wrapup subcommand
    wrapup_parser = subparsers.add_parser('wrapup', parents=[parent_parser], help='Commit the status of the current issue branch and push it to the remote',)
    wrapup_parser.add_argument('-m', '--message', type=str, help='Message for the commit', required=True)

    # Add deliver subcommand
    deliver_parser = subparsers.add_parser(
        'deliver', 
        parents=[parent_parser], help="Create a collapsed 'ready' branch for the current issue branch and push it to the remote",
        description="""
            Squeezes the issue branch into one commit and pushes it to the remote on separate "ready/*" branch.
            A seperate workflow should be defined for ready branches. The command takes no parameters.
            Policies for the delivery can be set in the configuration file '.tt-config.json'. Consult the README
            in 'thetechcollective/gh-tt' for details.
            """)
    
    #Add the responsibles subcommand
    responsibles_parser = subparsers.add_parser(
        'responsibles', 
        parents=[parent_parser], 
        help="List the responsibles for the current issue branch",
        description="""
            Lists the responsibles for the current change set""")
    responsibles_parser.add_argument('--unstaged', action='store_true', help='Get the list of responsibles for all dirty, but unstaged changes', required=False, default=False)
    responsibles_parser.add_argument('--staged',  action='store_true', help='Get the list of responsibles for staged changes', required=False, default=False)
    responsibles_parser.add_argument('--exclude', type=str, help="Comma separated list of handles to exclude '@me' is supported too", required=False, default=None)
    responsibles_parser.set_defaults(command='responsibles')

    # Add the semver subcommand
    semver_parser = subparsers.add_parser(
        'semver', 
        parents=[parent_parser, prerelease_parser], 
        help="Reads and sets the current version of the repo in semantic versioning format",
        description="""
            Supports reading and setting the current version of the repository in semantic 
            versioning format in both 'release' and 'prerelease' context.  Versions are stored as 
            tags in the repository.
            """)
    
    semver_sub_parser = semver_parser.add_subparsers(dest='semver_command')
    semver_bump_parser = semver_sub_parser.add_parser('bump', parents=[parent_parser, prerelease_parser], help="Bumps the current version of the repository in semantic versioning format")
    semver_bump_level_group = semver_bump_parser.add_mutually_exclusive_group(required=True)
    semver_bump_level_group.add_argument('--major', dest='level',  help='Bump the major version, breaking change', action='store_const', const='major')
    semver_bump_level_group.add_argument('--minor', dest='level',  help='Bump the minor version, new feature, non-breaking change', action='store_const', const='minor')
    semver_bump_level_group.add_argument('--patch', dest='level',  help='Bump the patch version, bug fix or rework, non-breaking change', action='store_const', const='patch')
    semver_bump_parser.add_argument('-m', '--message', type=str, help='Additional message for the annotated tag', required=False, default=None)
    semver_bump_parser.add_argument('--suffix', type=str, help='Suffix to use for prerelease tags', required=False, default=None)
    semver_bump_parser.add_argument('--prefix', type=str, help='Prefix to prepend the tag valid for both releases and prereleases', required=False, default=None)
    semver_bump_parser.add_argument('--initial', type=str, help='Initial off-set, only relevant if there are not tags defined. Bust be a three-level-interger seperated by dots.', required=False, default=None)
    run_group = semver_bump_parser.add_mutually_exclusive_group()
    run_group.add_argument('--run', dest='run', action='store_true', help='Execute the command')
    run_group.add_argument('--no-run', dest='run', action='store_false', help='Print the command without executing it')
    semver_bump_parser.set_defaults(run=True, exclusive_groups=['bump'])
    semver_list_parser = semver_sub_parser.add_parser('list', parents=[parent_parser, prerelease_parser], help="Lists the version tags in the repository in semantic versioning format and sort order in either prerelease or release context")
    semver_note_parser = semver_sub_parser.add_parser('note', parents=[parent_parser, prerelease_parser], help="Generates a release note either for a release or a prerelease, based on the set of current semver tags")
    semver_note_parser.add_argument('--filename', type=str, help='If provided, the note will be written to this file. If None, it will be printed to stdout.', required=False, default=None)

    args = parser.parse_args(args)

    if args.command == "workon" and args.reopen and not args.issue:
        parser.error("🛑 --reopen flag can only be used with the `workon --issue` command")

    if not args.command and not args.version:
        parser.print_help()
        parser.exit(0)

    if args.command == 'responsibles' and not (args.unstaged or args.staged):
        parser.error("You must specify either --unstaged or --staged  or both for the responsibles command")

    return args

def main():
    args = parse(sys.argv[1:])

    Gitter.verbose(verbose=args.verbose)
    Gitter.validate_gh_version()

    if args.version:
        Gitter.version()
        sys.exit(0)

    Gitter.read_cache()
    Gitter.validate_gh_scope(scope='project')
    
    devbranch = Devbranch()
    
    if args.command == 'workon':
        label = None

        if args.type is not None:
            Label.validate(args.type, "type")

        if args.issue:
            if label is None:
                try:
                    label = Config()._config_dict['workon']['default_type_labels']['issue']
                except KeyError:
                    pass

            devbranch.set_issue(issue_number=args.issue, assign=args.assignee, msg=args.body, reopen=args.reopen, label=label)
            
        elif args.title:
            if label is None:
                try:
                    label = Config()._config_dict['workon']['default_type_labels']['title']
                except KeyError:
                    pass
            issue =  Issue.create_new(title=args.title, body=args.body)
            devbranch.set_issue(issue_number=issue.get('number'), assign=args.assignee, reopen=args.reopen, label=label)
          
    if args.command == 'wrapup':
        devbranch.wrapup(message=args.message)
    
    if args.command == 'deliver':
        devbranch.deliver()

    if args.command == 'responsibles':
       devbranch.responsibles(unstaged=args.unstaged, staged=args.staged, exclude=args.exclude)

    if args.command == 'semver':
        if args.semver_command == 'bump':
            semver = Semver()
            semver.bump(
                level=args.level, 
                message=args.message, 
                suffix=args.suffix, 
                prefix=args.prefix, 
                initial=args.initial, 
                prerelease=args.prerelease, 
                dry_run=not args.run
            )

        elif args.semver_command == 'list':
            semver = Semver()
            semver.list(prerelease=args.prerelease)

        elif args.semver_command == 'note':
            semver = Semver()
            if args.filename:
                note = semver.note(prerelease=args.prerelease, filename=args.filename)
                print(f"{args.filename}")
            else:
                note = semver.note(prerelease=args.prerelease)
                print(note)

        elif args.semver_command is None:
            current_semver = Semver().get_current_semver(prerelease=args.prerelease)
            print(f"{current_semver}")
            
    Gitter.write_cache()            
    exit(0)
