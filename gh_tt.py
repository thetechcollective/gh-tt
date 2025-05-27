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
from project import Project
from gitter import Gitter
from issue import Issue

def parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog='gh tt', 
        parents=[parent_parser],
        description="""
            A command-line tool to support a consistent workflow across among a team. 
            It supports a number of subcommands which defines the entiner process: `workon`,
            `wrapup`, `deliver`  use the `-h|--help` switch on each to learn more. It utilizes 
            the GitHub API `gh` to interact with GtiHub and therefore it's provided as a gh extension. 
            GitHub Project integration is supporte4d. It enabels the issues to autoamtically 
            propregate through the columns in the (kanban) board. Please consult the README.md file 
            in 'thetechcollective/gh-tt' for more information on how to enable this feature 
            - and many more neat tricks.  
            """,)

    subparsers = parser.add_subparsers(dest='command')
    # Add workon subcommand
    workon_parser = subparsers.add_parser('workon', parents=[parent_parser], help='Set the issue number context to work on')
    workon_group = workon_parser.add_mutually_exclusive_group()
    workon_group.add_argument('-i', '--issue', type=int, help='Issue number')
    workon_group.add_argument('-t', '--title', type=str, help='Title for the new issue')
    assign_group = workon_parser.add_mutually_exclusive_group()
    assign_group.add_argument('--assign', dest='assignee', action='store_true', help='Assign @me to the issue (default)')
    assign_group.add_argument('--no-assign', dest='assignee', action='store_false', help='Do not assign anybody to the issue')
    workon_parser.set_defaults(assignee=True, exclusive_groups=['workon'])
    
    # Add wrapup subcommand
    wrapup_parser = subparsers.add_parser('wrapup', parents=[parent_parser], help='Collapse dev branch into one commit, check or set the commit message')
#   wrapup_parser.add_argument('-m', '--message', type=str, help='Message for the commit')

    # Add deliver subcommand
    deliver_parser = subparsers.add_parser(
        'deliver', 
        parents=[parent_parser], help="Create a collapsed 'ready' branch for the current issue branch and push it to the remote",
        description="""
            It squeezes the issue branch into just one commit and pushes it to the remote, with the same name as the issue brance as base, 
            but prefixed with 'ready/*'. A seperate workflow should be defined for ready branches. It dosen't take any parameters; Policies 
            for the delivery can be set in the configuration file '.tt-config.json'. Consult the README in 'thetechcollective/gh-tt' for 
            details.""")
    
    args = parser.parse_args(args)
    return args

if __name__ == "__main__":
    args = parse(sys.argv[1:])

    Gitter.verbose(verbose=args.verbose)
    Gitter.read_cache()
    Gitter.validate_gh_version()
    Gitter.validate_gh_scope(scope='project')
    
    devbranch = Devbranch()
    
    if args.command == 'workon':
        if args.issue:
            devbranch.set_issue(issue_number=args.issue, assign=args.assignee)
            
        elif args.title:
            issue =  Issue.create_new(title=args.title)
            devbranch.set_issue(issue_number=issue.get('number'), assign=args.assignee)
          
    if args.command == 'wrapup':
        devbranch.collapse()
    
    if args.command == 'deliver':
        devbranch.deliver()
            
    Gitter.write_cache()            
    exit(0)
