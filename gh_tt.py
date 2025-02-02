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

def validate_suffix(suffix):
    if not re.match("^[a-z0-9_-]*$", suffix):
        raise argparse.ArgumentTypeError("Suffix: Allowed characters are lowercase letters, numbers, dashes and underscores")
    return suffix

def validate_prefix(prefix):
    if not re.match("^[a-zA-z]*$", prefix):
        raise argparse.ArgumentTypeError("Prefix: Allowed characters are lowercase and uppercase letters")
    return prefix

def validate_initial(initial):
    if not re.match(r"^\d+\.\d+\.\d+$", initial):
        raise argparse.ArgumentTypeError("Initial offset: Must be a three-level integer separated by dots (e.g. 1.0.0)")
    return initial

def parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    # Define command-line arguments
    parser = argparse.ArgumentParser(parents=[parent_parser])

    # Create two subcommands - bump and config
    subparsers = parser.add_subparsers(dest='command')

    # Add workon subcommand
    workon_parser = subparsers.add_parser('workon', parents=[parent_parser], help='Set the issue number context to work on')
    workon_group = workon_parser.add_mutually_exclusive_group()
    workon_group.add_argument('-i', '--issue', type=int, help='Issue number')
    workon_group.add_argument('-t', '--title', type=str, help='Title for the new issue')
    workon_parser.set_defaults(exclusive_groups=['workon'])
    
    # Add wrapup subcommand
    wrapup_parser = subparsers.add_parser('wrapup', parents=[parent_parser], help='Collapse dev branch into one commit, rebase and create PR if needed')
    wrapup_parser.add_argument('-m', '--message', type=str, help='Message for the commit')

    # Add comment subcommand
    comment_parser = subparsers.add_parser('comment', parents=[parent_parser], help='Add a comment to the issue related to the dev branch')
    comment_parser.add_argument('-m', '--message', type=str, help='Comment message')

    args = parser.parse_args(args)
    return args


if __name__ == "__main__":
    args = parse(sys.argv[1:])
    
    devbranch = Devbranch(verbose=args.verbose)
    
    if args.command == 'workon':
        if args.issue:
            devbranch.set_issue(args.issue)
            if args.verbose:
                pprint.pprint(devbranch.props)
        elif args.title:
            issue =  devbranch.create_issue(args.title)
            devbranch.set_issue(issue)            
            if args.verbose:
                pprint.pprint(devbranch.props)
            
    if args.command == 'wrapup':
        devbranch.collapse()
        if args.verbose:
            pprint.pprint(devbranch.props)
    
    if args.command == 'comment':
        print( "Subcommand 'comment' is not implemented yet\nWhile you wait, you can use the GitHub ClI like this:\n$ gh issue comment <issue_number> -b '<comment>'")
    
    exit(0)
