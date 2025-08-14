import argparse

import pytest
from pytest_mock import MockerFixture

from gh_tt.classes.config import Config
from gh_tt.modules.tt_handlers import handle_deliver, handle_wrapup


@pytest.mark.unittest
@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_wrapup_with_poll_called_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="wrapup", poll=True, message="hi", message_by_flag=None)
    Config.config()["wrapup"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_called_once()


@pytest.mark.unittest
@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_wrapup_with_no_poll_did_not_call_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="wrapup", poll=False, message="hi", message_by_flag=None)
    Config.config()["wrapup"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_not_called()


@pytest.mark.unittest
def test_handlers_wrapup_poll_config_true(mocker: MockerFixture):
    args = argparse.Namespace(command="wrapup", message="hi", message_by_flag=None, poll=None)
    Config.config()["wrapup"]["policies"]["poll"] = True

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.wrapup")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_wrapup(args)

    mocked_poll.assert_called_once()


@pytest.mark.unittest
@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_deliver_with_poll_called_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="deliver", poll=True, message="hi", message_by_flag=None)
    Config.config()["deliver"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.deliver")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_deliver(args)

    mocked_poll.assert_called_once()


@pytest.mark.unittest
@pytest.mark.parametrize("config_value", [True, False])
def test_handlers_deliver_with_no_poll_did_not_call_poll_regardless_of_config(mocker: MockerFixture, config_value):
    args = argparse.Namespace(command="deliver", poll=False, message="hi", message_by_flag=None)
    Config.config()["deliver"]["policies"]["poll"] = config_value

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.deliver")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_deliver(args)

    mocked_poll.assert_not_called()


@pytest.mark.unittest
def test_handlers_deliver_poll_config_true(mocker: MockerFixture):
    args = argparse.Namespace(command="deliver", message="hi", message_by_flag=None, poll=None)
    Config.config()["deliver"]["policies"]["poll"] = True

    mocker.patch("gh_tt.modules.tt_handlers.Devbranch.deliver")
    mocked_poll = mocker.patch("gh_tt.modules.tt_handlers.Status.poll")

    handle_deliver(args)

    mocked_poll.assert_called_once()
