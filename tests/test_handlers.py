import argparse

import pytest

from gh_tt.cli.tt_handlers import handle_deliver, handle_workon


def test_workon_aborts_without_pr_workflow():
    args = argparse.Namespace(command='workon', pr_workflow=False)

    with pytest.raises(SystemExit):
        handle_workon(args)


def test_deliver_aborts_without_pr_workflow():
    args = argparse.Namespace(command='deliver', pr_workflow=False)

    with pytest.raises(SystemExit):
        handle_deliver(args)
