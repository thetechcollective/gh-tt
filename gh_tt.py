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

def parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    # Define command-line arguments
    parser = argparse.ArgumentParser(prog='gh tt', parents=[parent_parser])

    # Create two subcommands - bump and config
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
    wrapup_parser = subparsers.add_parser('wrapup', parents=[parent_parser], help='Collapse dev branch into one commit, rebase and create PR if needed')
#   wrapup_parser.add_argument('-m', '--message', type=str, help='Message for the commit')

    # Add comment subcommand
#   comment_parser = subparsers.add_parser('comment', parents=[parent_parser], help='Add a comment to the issue related to the dev branch')
#   comment_parser.add_argument('-m', '--message', type=str, help='Comment message')

    args = parser.parse_args(args)
    return args


if __name__ == "__main__":
    args = parse(sys.argv[1:])

    Gitter.read_cache()  
    devbranch = Devbranch(verbose=args.verbose)
    
    if args.command == 'workon':
        if args.issue:
            devbranch.set_issue(issue_number=args.issue, assign=args.assignee)
            
        elif args.title:
            issue =  devbranch.create_issue(args.title, args.assignee)
            devbranch.set_issue(issue_number=issue, assign=args.assignee)
          
    if args.command == 'wrapup':
        devbranch.collapse()

    
    if args.command == 'comment':
        print( "Subcommand 'comment' is not implemented yet\nWhile you wait, you can use the GitHub ClI like this:\n$ gh issue comment <issue_number> -b '<comment>'")
            
    Gitter.write_cache()            
    exit(0)
