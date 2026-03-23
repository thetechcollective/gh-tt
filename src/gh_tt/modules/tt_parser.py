import argparse


def tt_parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='count', help='Enable verbose output. -v for INFO, -vv for DEBUG', default=0)
    parent_parser.add_argument('--pr-workflow', action='store_true', help='Migration flag to ease transition to a new workflow', default=False, dest='pr_workflow')

    version_parser = argparse.ArgumentParser(add_help=False)
    version_parser.add_argument('--version', action='store_true', help='Print version information and exit')

    poll_parser = argparse.ArgumentParser(add_help=False)
    poll_group = poll_parser.add_mutually_exclusive_group()
    poll_group.add_argument('--poll', dest='poll', action='store_true', help='Poll the status until it is set to success or failure (default)')
    poll_group.add_argument('--no-poll', dest='poll', action='store_false', help='Do not continue to poll the status, just fire and forget')
    poll_parser.set_defaults(poll=None)
    
    # Define command-line arguments
    parser = argparse.ArgumentParser(
        prog='gh tt', 
        parents=[parent_parser, version_parser],
        description="""
            A command-line tool to support a consistent team workflow. 
            It supports a number of subcommands which define the entire process: `workon`,
            `deliver`.  Use the `-h|--help` switch on each to learn more. The extension utilizes 
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
    workon_parser.add_argument('-b', '--body', dest='body', type=str, help='Optional body (issue comment) for the new issue')

    assign_group = workon_parser.add_mutually_exclusive_group()
    assign_group.add_argument('--assign', dest='assignee', action='store_true', help='Assign @me to the issue (default)')
    assign_group.add_argument('--no-assign', dest='assignee', action='store_false', help='Do not assign anybody to the issue')
    workon_parser.set_defaults(assignee=True, exclusive_groups=['workon'])

    # Add deliver subcommand
    deliver_parser = subparsers.add_parser(
        'deliver', 
        parents=[parent_parser, poll_parser], help="Enable auto merge on the PR",
        description="""
            Enables auto merge on the PR connected to the current branch. Should be used
            in combination with a branch protection check which will merge only PRs
            that passing the integration pipeline.
            """)
    deliver_parser.add_argument('-d,', '--delete-branch', action='store_true', dest='delete_branch', default=False, help='Delete branch after the PR is merged. Only supported with the --pr-workflow flag.')

    # Add the semver subcommand
    semver_parser = subparsers.add_parser(
        'semver', 
        parents=[parent_parser], 
        help="Reads and sets the current version of the repo in semantic versioning format",
        description="""
            Supports reading and setting the current version of the repository in semantic 
            versioning format.  Versions are stored as tags in the repository.
            """)
    
    # Add option to show prerelease version when no subcommand is used
    semver_parser.add_argument('--prerelease', '--pre', action='store_true',
                              help='Show the highest prerelease version instead of the highest release version', 
                              default=False)
    
    semver_sub_parser = semver_parser.add_subparsers(dest='semver_command')
    semver_bump_parser = semver_sub_parser.add_parser('bump', parents=[parent_parser], help="Bumps the current version of the repository in semantic versioning format")
    semver_bump_level_group = semver_bump_parser.add_mutually_exclusive_group(required=True)
    semver_bump_level_group.add_argument('--major', dest='level',  help='Bump the major version, breaking change', action='store_const', const='major')
    semver_bump_level_group.add_argument('--minor', dest='level',  help='Bump the minor version, new feature, non-breaking change', action='store_const', const='minor')
    semver_bump_level_group.add_argument('--patch', dest='level',  help='Bump the patch version, bug fix or rework, non-breaking change', action='store_const', const='patch')
    semver_bump_level_group.add_argument('--prerelease', '--pre', dest='level',  help='Bump the prerelease version', action='store_const', const='prerelease')
    semver_bump_level_group.add_argument('--build', dest='level',  help='Bump the build version', action='store_const', const='build')
    semver_bump_parser.add_argument('-m', '--message', type=str, help='Additional message for the annotated tag', required=False, default=None)
    semver_bump_parser.add_argument('--prefix', type=str, help='Prefix to prepend the tag valid for both releases and prereleases', required=False, default=None)
    semver_bump_parser.add_argument('--no-sha', dest='include_sha', action='store_false', help='Do not include git SHA in build number (only valid with --build)', required=False, default=True)
    run_group = semver_bump_parser.add_mutually_exclusive_group()
    run_group.add_argument('--run', dest='run', action='store_true', help='Execute the command')
    run_group.add_argument('--no-run', dest='run', action='store_false', help='Print the command without executing it')
    semver_bump_parser.set_defaults(run=True, exclusive_groups=['bump'])
    
    # List command with filter options
    semver_list_parser = semver_sub_parser.add_parser('list', parents=[parent_parser], help="Lists the version tags in the repository in semantic versioning format and sort order")
    list_filter_group = semver_list_parser.add_mutually_exclusive_group()
    list_filter_group.add_argument('--release', dest='filter_type', action='store_const', const='release', help='Show only release versions')
    list_filter_group.add_argument('--prerelease', '--pre', dest='filter_type', action='store_const', const='prerelease', help='Show only prerelease versions')
    list_filter_group.add_argument('--other', dest='filter_type', action='store_const', const='other', help='Show only non-semantic version tags')
    list_filter_group.add_argument('--all', dest='filter_type', action='store_const', const='all', help='Show all version tags (default)')
    semver_list_parser.add_argument('--sha', action='store_true', help='Show commit SHAs for each version tag', default=False)
    semver_list_parser.set_defaults(filter_type='all')
    semver_note_parser = semver_sub_parser.add_parser('note', parents=[parent_parser], help="Generates a release note based on the set of current semver tags")
    semver_note_parser.add_argument('--filename', type=str, help='If provided, the note will be written to this file. If None, it will be printed to stdout.', required=False, default=None)
    semver_note_parser.add_argument('--from', dest='from_ref', type=str, help='Starting reference for the release note. Defaults to the previous release tag.', required=False, default=None)
    semver_note_parser.add_argument('--to', dest='to_ref', type=str, help='Ending reference for the release note. Defaults to the current release tag or HEAD.', required=False, default=None)

    args = parser.parse_args(args)

    if not args.command and not args.version:
        parser.print_help()
        parser.exit(0)
        
    # Validate that --no-sha is only used with --build
    if hasattr(args, 'include_sha') and args.include_sha is False and (not hasattr(args, 'level') or args.level != 'build'):
        semver_bump_parser.error("🛑 The --no-sha flag can only be used with the --build level")

    if args.command == 'deliver' and (not args.pr_workflow and args.delete_branch):
        deliver_parser.error("🛑 The --delete-branch flag can only be used with the --pr-workflow flag")

    return args
