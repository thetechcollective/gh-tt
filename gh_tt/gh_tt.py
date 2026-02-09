#!/usr/bin/env python3

import sys

from gh_tt.classes.gitter import Gitter
from gh_tt.modules.tt_handlers import COMMAND_HANDLERS
from gh_tt.modules.tt_parser import tt_parse


def main():
    args = tt_parse(sys.argv[1:])

    Gitter.set_verbose(value=args.verbose)
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
