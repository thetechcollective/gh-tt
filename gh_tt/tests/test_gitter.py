import asyncio

import pytest

from gh_tt.classes.gitter import Gitter


@pytest.mark.unittest
def test_gitter_validate_gh_version_success(mocker):
    stdout = "gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0"

    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(stdout, mocker.Mock()),
        new_callable=mocker.AsyncMock
    )

    assert Gitter.validate_gh_version()


@pytest.mark.unittest
def test_gitter_validate_gh_version_failure(mocker, capsys):
    stdout = "gh version 2.54.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.54.0"

    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(stdout, mocker.Mock()),
        new_callable=mocker.AsyncMock
    )

    with pytest.raises(SystemExit) as cm:
        Gitter.validate_gh_version()

    assert cm.value.code == 1
    assert f"gh version 2.54.0 is not supported. Please upgrade to version {Gitter.required_version} or higher\n" in capsys.readouterr().err

@pytest.mark.unittest
def test_gitter_validate_gh_scope_success(mocker):
    stdout = """github.com
✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
- Active account: true
- Git operations protocol: https
- Token: gho_************************************
- Token scopes: 'gist', 'read:org', 'repo', 'project', 'workflow'"""
    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(stdout, mocker.Mock()),
        new_callable=mocker.AsyncMock
    )

    assert Gitter.validate_gh_scope(scope="project")

@pytest.mark.unittest
def test_gitter_validate_gh_scope_ignores_ghs(mocker):
    stdout = """github.com
✓ Logged in to github.com account gh-tt-qa-runner[bot] (GH_TOKEN)
- Active account: true
- Git operations protocol: https
- Token: ghs_************************************"""
    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(stdout, mocker.Mock())
    )
            
    assert Gitter.validate_gh_scope(scope="project")
    
@pytest.mark.unittest
def test_gitter_validate_gh_scope_failure(mocker, capsys):
    stdout = """github.com
✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
- Active account: true
- Git operations protocol: https
- Token: gho_************************************
- Token scopes: 'gist', 'read:org', 'repo', 'read:project', 'workflow'"""
    
    value="project"

    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(stdout, mocker.Mock())
    )

    with pytest.raises(SystemExit) as cm:
        Gitter.validate_gh_scope(scope=value)

    assert cm.value.code == 1
    assert f"gh token does not have the required scope '{value}'" in capsys.readouterr().err

@pytest.mark.unittest
def test_gitter_fetch(mocker):
    mock_gitter_run = mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=("", mocker.Mock()),
        new_callable=mocker.AsyncMock
    )

    Gitter.fetched = True
    result_1 = asyncio.run(Gitter.fetch())                              
    assert result_1
    mock_gitter_run.assert_not_called()
    mock_gitter_run.reset_mock()

    Gitter.fetched = True
    result_2 = asyncio.run(Gitter.fetch(again=True))                              
    assert result_2
    mock_gitter_run.assert_called_once_with()
    mock_gitter_run.reset_mock()

    Gitter.fetched = False
    result_3 = asyncio.run(Gitter.fetch(prune=True, again=False))
    assert result_3
    mock_gitter_run.assert_called_once_with()
    mock_gitter_run.reset_mock()

    Gitter.fetched = False
    result_4 = asyncio.run(Gitter.fetch(prune=True, again=False))
    assert result_4
    mock_gitter_run.assert_called_once_with()

@pytest.mark.unittest
def test_run_success(mocker):
    mock_process = mocker.AsyncMock()
    mock_process.communicate.return_value = (
        b'fa05229e20052cbb1a13d0c6ee9da7115df55b89',
        b''
    )
    mock_process.returncode = 0
    
    mock_create_subprocess_shell = mocker.patch(
        'asyncio.create_subprocess_shell',
        return_value=mock_process,
        new_callable=mocker.AsyncMock
    )

    gitter = Gitter(cmd="git rev-parse HEAD", msg="Get current commit hash")
    value, result = asyncio.run(gitter.run())

    assert value == 'fa05229e20052cbb1a13d0c6ee9da7115df55b89'
    mock_create_subprocess_shell.assert_called_once_with(
        cmd="git rev-parse HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=gitter.get('workdir')
    )
    assert result['returncode'] == 0
    assert gitter.get('msg') == "Get current commit hash"
    assert gitter.get('cmd') == "git rev-parse HEAD"
