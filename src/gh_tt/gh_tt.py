#!/usr/bin/env python3
import logging
import sys

from gh_tt.classes.gitter import Gitter
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
    Gitter.validate_gh_version()

    if args.version:
        logger.debug('printing version and exiting')
        Gitter.version()
        sys.exit(0)

    Gitter.read_cache()
    Gitter.validate_gh_scope(scope='project')

    if args.command in COMMAND_HANDLERS:
        logger.debug('dispatching command: %s', args.command)
        COMMAND_HANDLERS[args.command](args)
    else:
        logger.debug('no command handler found for: %s', args.command)

    Gitter.write_cache()
    sys.exit(0)
