#!/usr/bin/env python3
import logging
import sys
import typing

from gh_tt.classes.gitter import Gitter
from gh_tt.modules.tt_handlers import COMMAND_HANDLERS
from gh_tt.modules.tt_parser import tt_parse


def setup_logging(verbose: int):
    match verbose:
        case 2:
            level = logging.DEBUG
        case 1:
            level = logging.INFO
        case int():
            level = logging.WARNING
        case _:
            typing.assert_never()

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
    )


def main():
    args = tt_parse(sys.argv[1:])

    setup_logging(args.verbose)

    legacy_gitter_verbose = args.verbose >= 1

    Gitter.set_verbose(value=legacy_gitter_verbose)
    Gitter.validate_gh_version()

    if args.version:
        Gitter.version()
        sys.exit(0)

    Gitter.read_cache()
    Gitter.validate_gh_scope(scope='project')

    # Execute the appropriate command handler
    if args.command in COMMAND_HANDLERS:
        COMMAND_HANDLERS[args.command](args)

    Gitter.write_cache()
    sys.exit(0)
