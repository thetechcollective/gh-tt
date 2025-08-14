import asyncio
import re

import pytest
from pytest_mock import MockerFixture

from gh_tt.classes.config import Config
from gh_tt.classes.devbranch import Devbranch
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.issue import Issue


@pytest.mark.unittest
def test_wrapup_responsibles_notifies_only_on_new_changes():
    issue = Issue().from_json(file="gh_tt/tests/data/issue/issue_responsibles_comment.json")
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch_responsibles_comment.json")
    comments = issue.get("comments")

    responsibles = devbranch._get_responsibles(issue_comments=comments)

    assert responsibles.find("tests/test_issue.py") == -1


@pytest.mark.unittest
def test_constructor_success():
    devbranch = Devbranch()
    assert devbranch.get("unstaged_changes") is None
    assert devbranch.get("staged_changes") is None
    assert devbranch.get("is_dirty") is None
    assert devbranch.get("issue_number") is None
    assert devbranch._manifest_loaded


@pytest.mark.unittest
def test_load_issue_number_success():
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/.tt-config-set_issue.json")
    asyncio.run(devbranch._load_issue_number())
    assert devbranch.get("issue_number") == "95"


@pytest.mark.unittest
def test_load_issue_number_none():
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/main.json")
    asyncio.run(devbranch._load_issue_number())
    assert devbranch.get("issue_number") is None
    assert devbranch.get("branch_name") == "main"


@pytest.mark.unittest
def test__reuse_issue_branch(mocker):
    mock_run = mocker.patch(
        "gh_tt.classes.devbranch.Devbranch._run",
        return_value="",
        new_callable=mocker.AsyncMock,
    )

    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/workon_reuse_issue_branch.json")

    # Create a single loop for all test cases
    loop = asyncio.new_event_loop()
    reuse_local = loop.run_until_complete(devbranch._Devbranch__reuse_issue_branch(7))
    assert reuse_local
    mock_run.assert_called_once_with(prop="checkout_local_branch")
    mock_run.reset_mock()

    devbranch.props["local_branches"] = ""
    reuse_remote = loop.run_until_complete(devbranch._Devbranch__reuse_issue_branch(7))
    assert reuse_remote
    mock_run.assert_called_once_with("checkout_remote_branch")
    mock_run.reset_mock()  # Reset the mock for the next call

    devbranch.props["remote_branches"] = ""
    reuse = loop.run_until_complete(devbranch._Devbranch__reuse_issue_branch(7))
    assert not reuse
    loop.close()


@pytest.mark.unittest
def test__compare_before_after_trees(mocker, capsys):
    mock_run = mocker.patch("gh_tt.classes.devbranch.Devbranch._run", new_callable=mocker.AsyncMock, side_effect=["", "somefile.txt"])

    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch-squeeze.json")

    # no diffs
    diff = devbranch._Devbranch__compare_before_after_trees()
    assert diff
    mock_run.assert_called_once_with("compare_trees")
    mock_run.reset_mock()

    # Some diffs
    with pytest.raises(SystemExit) as cm:
        devbranch._Devbranch__compare_before_after_trees()

    assert cm.value.code == 1
    assert re.search(r"FATAL:\nThe squeezed commit tree (.*) is not identical to the one on the issue branch", capsys.readouterr().err)
    mock_run.assert_called_once_with("compare_trees")
    mock_run.reset_mock()


@pytest.mark.unittest
def test__load_squeezed_commit_message():
    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch-squeeze.json")

    message = devbranch._Devbranch__load_squeezed_commit_message()
    assert re.search(r"^Add support for .*ready.*resolves #91", message)
    assert re.search(r".*a201d0f.*", message)


@pytest.mark.unittest
def test__squeeze_exits(capsys):
    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch-squeeze.json")

    # Create a single loop for all test cases
    loop = asyncio.new_event_loop()
    # no diffs

    with pytest.raises(SystemExit) as cm:
        loop.run_until_complete(devbranch._Devbranch__squeeze())

    assert cm.value.code == 1
    assert "ERROR: There are staged changes" in capsys.readouterr().err

    Config._config_dict["squeeze"]["policies"]["allow-dirty"] = False

    with pytest.raises(SystemExit) as cm:
        loop.run_until_complete(devbranch._Devbranch__squeeze())

    assert cm.value.code == 1
    assert "ERROR: The working directory is not clean" in capsys.readouterr().err

    Config._config_dict["squeeze"]["policies"]["abort_for_rebase"] = False
    Config._config_dict["squeeze"]["policies"]["allow-dirty"] = True
    Config._config_dict["squeeze"]["policies"]["quiet"] = False
    Config._config_dict["squeeze"]["policies"]["allow-staged"] = False

    with pytest.raises(SystemExit) as cm:
        loop.run_until_complete(devbranch._Devbranch__squeeze())

    assert cm.value.code == 1
    assert "ERROR: There are staged changes" in capsys.readouterr().err

    Config._config_dict["squeeze"]["policies"]["abort_for_rebase"] = True
    devbranch.props["merge_base"] = "490e2075ca58113619e026ab53bdfc719e56b375"

    with pytest.raises(SystemExit) as cm:
        loop.run_until_complete(devbranch._Devbranch__squeeze())

    assert cm.value.code == 1
    assert re.search(r"ERROR: The .* branch has commits your branch has never seen.", capsys.readouterr().err)

    loop.close()


@pytest.mark.unittest
def test__squeeze_success(mocker):
    mock_assert_props = mocker.patch("gh_tt.classes.devbranch.Devbranch._assert_props", new_callable=mocker.AsyncMock)
    mocker.patch("gh_tt.classes.devbranch.Devbranch._Devbranch__compare_before_after_trees", return_value=True)

    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch-squeeze.json")

    Config._config_dict["squeeze"]["policies"]["abort_for_rebase"] = False
    Config._config_dict["squeeze"]["policies"]["allow-dirty"] = True
    Config._config_dict["squeeze"]["policies"]["quiet"] = False
    Config._config_dict["squeeze"]["policies"]["allow-staged"] = True
    devbranch.props["_loaded"] = ["init", "remote-init", "branch_reuse", "pre-squeeze"]

    squeezed_sha = devbranch._Devbranch__squeeze()

    assert squeezed_sha == "e4bba5cbd37f72b64c647f3504c7fac66518ab9f"
    mock_assert_props.assert_called_with(["squeeze_sha1"])


@pytest.mark.unittest
def test_load_status(mocker):
    mock_force_prop_reload = mocker.patch("gh_tt.classes.devbranch.Devbranch._force_prop_reload", new_callable=mocker.AsyncMock, return_value=None)

    Gitter.verbose = True
    # Load the recorded instance of Devbranch
    devbranch = Devbranch().from_json(file="gh_tt/tests/data/devbranch/devbranch-squeeze.json")

    # no diffs
    assert devbranch.get("unstaged_changes") is None
    assert devbranch.get("staged_changes") is None
    assert devbranch.get("is_dirty") is None

    devbranch._load_status()

    assert devbranch.get("is_dirty")

    assert "MM .github/workflows/python-app.yml" in devbranch.get("staged_changes")
    assert "M  gh_tt.py" in devbranch.get("staged_changes")

    assert " M classes/gitter.py" in devbranch.get("unstaged_changes")
    assert "?? tests/test_config.py" in devbranch.get("unstaged_changes")

    # Run again, to check if it is cached (nothing is change but used to get coverage on the retun-when-already-loaded branch)
    devbranch._load_status()

    devbranch._load_status(reload=True)
    mock_force_prop_reload.assert_called_once_with("status")

@pytest.mark.unittest
def test_wrapup_only_on_issue_branch(mocker: MockerFixture, capsys):
    devbranch = Devbranch()

    mocker.patch('gh_tt.classes.devbranch.Devbranch._assert_props')
    mocker.patch('gh_tt.classes.devbranch.Devbranch._run')
    mocker.patch('gh_tt.classes.devbranch.Devbranch._push')
    mocker.patch('gh_tt.classes.devbranch.Devbranch._load_status')
    mocker.patch('gh_tt.classes.issue.Issue')

    devbranch.set('issue_number', None)
    devbranch.set('branch_name', 'not-an-issue-branch')

    with pytest.raises(SystemExit) as cm:
        devbranch.wrapup('msg')

    assert cm.value.code == 1
    assert 'Wrapup is supported only on branches named <issue number>-<branch_name>' in capsys.readouterr().err
