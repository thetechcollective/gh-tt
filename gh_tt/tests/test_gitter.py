import asyncio
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from gh_tt.classes.gitter import Gitter


@pytest.mark.unittest
def test_gitter_validate_gh_version_success(monkeypatch):
    async def mock_result(*args, **kwargs):
        return "gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0"

    monkeypatch.setattr(Gitter, "_run", mock_result)

    assert Gitter.validate_gh_version()


@pytest.mark.unittest
def test_gitter_validate_gh_version_failure(monkeypatch, capsys):
    async def mock_result(*args, **kwargs):
        return "gh version 2.54.0 (2024-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.54.0"
    
    monkeypatch.setattr(Gitter, "_run", mock_result)

    with pytest.raises(SystemExit) as cm:
        Gitter.validate_gh_version()

    assert cm.value.code == 1
    assert f"gh version 2.54.0 is not supported. Please upgrade to version {Gitter.required_version} or higher\n" in capsys.readouterr()

@pytest.mark.unittest
@patch('gh_tt.classes.gitter.Gitter.run',new_callable=AsyncMock)
def test_gitter_validate_gh_scope_success(self, mock_gitter_run):
    stdout = """github.com
✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
- Active account: true
- Git operations protocol: https
- Token: gho_************************************
- Token scopes: 'gist', 'read:org', 'repo', 'project', 'workflow'"""
    result_mock = Mock(returncode=0, stderr="")
    mock_gitter_run.return_value = (stdout, result_mock)             
            
    valid = Gitter.validate_gh_scope(scope="project")
    self.assertTrue(valid)

@pytest.mark.unittest
@patch('gh_tt.classes.gitter.Gitter.run',new_callable=AsyncMock)
def test_gitter_validate_gh_scope_ignores_ghs(self, mock_gitter_run):
    stdout = """github.com
✓ Logged in to github.com account gh-tt-qa-runner[bot] (GH_TOKEN)
- Active account: true
- Git operations protocol: https
- Token: ghs_************************************"""
    result_mock = Mock(returncode=0, stderr="")
    mock_gitter_run.return_value = (stdout, result_mock)             
            
    valid = Gitter.validate_gh_scope(scope="project")
    self.assertTrue(valid)
    
@pytest.mark.unittest
@patch('gh_tt.classes.gitter.Gitter.run',new_callable=AsyncMock)
def test_gitter_validate_gh_scope_failure(self, mock_gitter_run):
    stdout = """github.com
✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
- Active account: true
- Git operations protocol: https
- Token: gho_************************************
- Token scopes: 'gist', 'read:org', 'repo', 'read:project', 'workflow'"""
    result_mock = Mock(returncode=0, stderr="")
    mock_gitter_run.return_value = (stdout, result_mock)     
    
    value="project"       
    with self.assertRaises(SystemExit) as cm:
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            valid = Gitter.validate_gh_scope(scope=value)
                            
    # Assertions
    self.assertEqual(cm.exception.code, 1)
    self.assertIn(f"gh token does not have the required scope '{value}'", mock_stderr.getvalue())  

@pytest.mark.unittest
@patch('gh_tt.classes.gitter.Gitter.run',new_callable=AsyncMock)
def test_gitter_fetch(self, mock_gitter_run):
    stdout = ""
    result_mock = Mock(returncode=0, stderr="")
    mock_gitter_run.return_value = (stdout, result_mock)     
    
    Gitter.fetched = True
    result = asyncio.run(Gitter.fetch())                              
    self.assertTrue(result)
    mock_gitter_run.assert_not_called()
    mock_gitter_run.reset_mock()

    Gitter.fetched = True
    result = asyncio.run(Gitter.fetch(again=True))                              
    self.assertTrue(result)
    mock_gitter_run.assert_called_once_with()
    mock_gitter_run.reset_mock()

    Gitter.fetched = False
    result1 = asyncio.run(Gitter.fetch(prune=True, again=False))
    self.assertTrue(result1)
    mock_gitter_run.assert_called_once_with()
    mock_gitter_run.reset_mock()

    Gitter.fetched = False
    result2 = asyncio.run(Gitter.fetch(prune=True, again=False))
    self.assertTrue(result2)
    mock_gitter_run.assert_called_once_with()

@pytest.mark.unittest
@patch('asyncio.create_subprocess_shell', new_callable=AsyncMock)
async def test_run_success(self, mock_create_subprocess_shell):
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (
        b'fa05229e20052cbb1a13d0c6ee9da7115df55b89',
        b''
    )
    mock_process.returncode = 0
    mock_create_subprocess_shell.return_value = mock_process

    gitter = Gitter(cmd="git rev-parse HEAD", msg="Get current commit hash")
    value, result = await gitter.run()

    self.assertEqual(value, 'fa05229e20052cbb1a13d0c6ee9da7115df55b89')
    mock_create_subprocess_shell.assert_called_once_with(
        cmd="git rev-parse HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=gitter.get('workdir')
    )
    self.assertEqual(result['returncode'], 0)
    self.assertEqual(gitter.get('msg'), "Get current commit hash")
    self.assertEqual(gitter.get('cmd'), "git rev-parse HEAD")
    