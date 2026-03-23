#!/usr/bin/env python3
import asyncio
import logging
import os
import sys

from gh_tt.classes.gitter import Gitter
from gh_tt.commands import gh
from gh_tt.modules.tt_handlers import COMMAND_HANDLERS
from gh_tt.modules.tt_parser import tt_parse

logger = logging.getLogger(__name__)


def setup_logging(verbose: int):
    match verbose:
        case v if v >= 2:
            level = logging.DEBUG
        case 1:
            level = logging.INFO
        case _:
            level = logging.WARNING

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
    )

    # logging.basicConfig could be a no-op if a logger is already configured
    # e.g. by pytest - so we explicitly set the level to preserve args.verbose
    logging.getLogger().setLevel(level=level)


def main():
    args = tt_parse(sys.argv[1:])

    setup_logging(args.verbose)
    logger.debug('parsed args: %s', args)

    legacy_gitter_verbose = args.verbose >= 1

    Gitter.set_verbose(value=legacy_gitter_verbose)

    gh_version = asyncio.run(gh.get_gh_cli_version())
    required_gh_version = '2.55.0'
    if gh_version < required_gh_version:
        print(
            f'gh version {gh_version} is not supported. Please upgrade to version {required_gh_version} or higher',
            file=sys.stderr,
        )
        sys.exit(1)

    if args.version:
        logger.debug('printing version and exiting')
        Gitter.version()
        sys.exit(0)

    Gitter.read_cache()

    gh_scopes = asyncio.run(gh.get_gh_auth_scopes())

    # Needed for end to end testing in GH workflows. When running in a GitHub action,
    # we use a GitHub App which is authorized in the workflow and does not have auth tokens.
    if not os.getenv('GITHUB_ACTIONS') and 'project' not in gh_scopes:
        print(
            "gh token does not have the required scope 'project'\nfix it by running:\n   gh auth refresh --scopes 'project'",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.command in COMMAND_HANDLERS:
        logger.debug('dispatching command: %s', args.command)
        COMMAND_HANDLERS[args.command](args)
    else:
        logger.debug('no command handler found for: %s', args.command)

    Gitter.write_cache()
    sys.exit(0)
