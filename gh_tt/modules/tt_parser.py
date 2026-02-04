import argparse


def tt_parse(args=None):
    # Define the parent parser with the --verbose argument
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output', default=False)
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
    wrapup_parser = subparsers.add_parser('wrapup', parents=[parent_parser, poll_parser], help='Commit the status of the current issue branch and push it to the remote',)
    wrapup_message_group = wrapup_parser.add_mutually_exclusive_group(required=True)
    wrapup_message_group.add_argument('message', nargs='?', help='Message for the commit (short hand positional option - no flag needed, mutually exclusive with -m|--message)')
    wrapup_message_group.add_argument('-m', '--message', dest='message_by_flag', type=str, help='Message for the commit')



    # Add deliver subcommand
    subparsers.add_parser(
        'deliver', 
        parents=[parent_parser, poll_parser], help="Create a collapsed 'ready' branch for the current issue branch and push it to the remote",
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

    # Add a status subcommand
    status_parser = subparsers.add_parser(
        'status', 
        parents=[parent_parser], 
        help="Set or get the status of a commit",
        description="""
            Set or get the status of a commit. The command supports setting the status with a state, description, context, and target URL.
            It also supports polling the status of a commit by its SHA.
            """)

    # Define a parent parser both set and get can use, that defines an optional --sha SHA
    status_parent_parser = argparse.ArgumentParser(add_help=False)
    status_parent_parser.add_argument('--sha', type=str, help='SHA of the commit. Default is HEAD', default=None)

    # Add two status sub commands; set and get    
    status_sub_parser = status_parser.add_subparsers(dest='status_command')
    status_set_parser = status_sub_parser.add_parser('set', help="Set the status of a commit", parents=[status_parent_parser])
    status_sub_parser.add_parser('get', help="Get the status of a commit", parents=[status_parent_parser])

    def valid_status_states(value):
        valid_states = ['success', 'failure', 'pending', 'queued']
        if value not in valid_states:
            raise argparse.ArgumentTypeError(f"Invalid state: {value}. Must be one of {', '.join(valid_states)}.")
        return value

    status_set_parser.add_argument('--state', type=valid_status_states, help='State of the commit status (success, failure, pending or queued)', required=True)
    status_set_parser.add_argument('--description', type=str, help='Description of the commit status', required=True)
    status_set_parser.add_argument('--context', type=str, help='Context (name) of the commit status. Can be omitted in context of a GitHub Action in which case it will default to the Action ID', default=None)
    status_set_parser.add_argument('--target-url', type=str, help='Target URL for the commit status. Can be omitted in context of a GitHub Action in which case it will default to the URL to the action run', default=None)

    # Sync subcommand
    sync_parser = subparsers.add_parser(
        'sync', 
        parents=[parent_parser],
        help="Sync GitHub items from a template repository to all sibling repositories"
    )

    sync_parser.add_argument('--labels', action='store_true', help='Read labels from the template repo and create them in all sibling repos')
    sync_parser.add_argument('--milestones', action='store_true', help='Read milestones from the template repo and create them in all sibling repos')

    args = parser.parse_args(args)

    if args.command == "workon" and args.reopen and not args.issue:
        parser.error("🛑 --reopen flag can only be used with the `workon --issue` command")

    if not args.command and not args.version:
        parser.print_help()
        parser.exit(0)

    if args.command == 'responsibles' and not (args.unstaged or args.staged):
        parser.error("You must specify either --unstaged or --staged  or both for the responsibles command")

    if args.command == 'sync' and not (args.labels or args.milestones):
        sync_parser.error("🛑 You must specify at least one entity (e.g. labels) to sync")
        
    # Validate that --no-sha is only used with --build
    if hasattr(args, 'include_sha') and args.include_sha is False and (not hasattr(args, 'level') or args.level != 'build'):
        semver_bump_parser.error("🛑 The --no-sha flag can only be used with the --build level")

    return args
