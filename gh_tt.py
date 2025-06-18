#!/usr/bin/env python3

import os
import sys
import argparse
import re
import pprint

# Add the subdirectory containing the classes to the general class_path
class_path = os.path.dirname(os.path.abspath(__file__)) + "/classes"
sys.path.append(class_path)

from devbranch import Devbranch
from gitter import Gitter
from issue import Issue
from config import Config

def parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog='gh tt', 
        parents=[parent_parser],
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
    
    #Add the responsibles suncommand
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
    # Add the project subcommand
    
    args = parser.parse_args(args)

    if not args.command:
        parser.print_help()
        parser.exit(0)

    if args.command == 'responsibles' and not (args.unstaged or args.staged):
        parser.error("You must specify either --unstaged or --staged  or both for the responsibles command")

    return args

if __name__ == "__main__":
    args = parse(sys.argv[1:])

    Gitter.verbose(verbose=args.verbose)
    Gitter.read_cache()
    Gitter.validate_gh_version()
    Gitter.validate_gh_scope(scope='project')
    
    devbranch = Devbranch()
    
    if args.command == 'workon':
        label = None

        if args.type is not None:
            is_valid_type_label = False
            for label_name, label_data in Config()._config_dict['labels'].items():
                if label_data["category"] == "type" and label_name == args.type:
                    is_valid_type_label = True
                    break

            if not is_valid_type_label:
                type_labels = [label_name for label_name, label_data in Config()._config_dict['labels'].items() if label_data["category"] == "type"]
                print(f"🛑  ERROR: \"{args.type}\" passed in --type is not matching any issue type labels defined in the config. Choose of the issue type labels defined: {type_labels}")
                sys.exit(1)

            label=args.type

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
            
    Gitter.write_cache()            
    exit(0)
