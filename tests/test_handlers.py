import argparse

import pytest
from pytest_mock import MockerFixture

from gh_tt.classes.config import Config
from gh_tt.modules.tt_handlers import handle_deliver, handle_workon, handle_wrapup


@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_wrapup_with_poll_called_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="wrapup", poll=True, message="hi", message_by_flag=None)
    Config.config()["wrapup"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_called_once()


@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_wrapup_with_no_poll_did_not_call_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="wrapup", poll=False, message="hi", message_by_flag=None)
    Config.config()["wrapup"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_not_called()


def test_handlers_wrapup_poll_config_true(mocker: MockerFixture):
    args = argparse.Namespace(command="wrapup", message="hi", message_by_flag=None, poll=None)
    Config.config()["wrapup"]["policies"]["poll"] = True

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_called_once()


def test_workon_aborts_without_pr_workflow():
    args = argparse.Namespace(command="workon", pr_workflow=False)

    with pytest.raises(SystemExit):
        handle_workon(args)


def test_deliver_aborts_without_pr_workflow():
    args = argparse.Namespace(command="deliver", pr_workflow=False)

    with pytest.raises(SystemExit):
        handle_deliver(args)