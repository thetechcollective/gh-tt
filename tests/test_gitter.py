import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest
from unittest.mock import AsyncMock
import asyncio

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from gitter import Gitter


class TestGitter(unittest.TestCase):

    @pytest.mark.unittest
    @patch('gitter.Gitter.run',new_callable=AsyncMock)
    def test_gitter_validate_gh_version_success(self, mock_gitter_run):
        # Setup
        stdout = "gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0"
        result_mock = Mock(returncode=0, stderr="")
        mock_gitter_run.return_value = (stdout, result_mock)
              
        valid = Gitter.validate_gh_version()
        self.assertTrue(valid)


    @pytest.mark.unittest
    @patch('gitter.Gitter.run',new_callable=AsyncMock)
    def test_gitter_validate_gh_version_failure(self, mock_gitter_run):
        stdout = "gh version 2.54.0 (2024-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.54.0"
        result_mock = Mock(returncode=0, stderr="")
        mock_gitter_run.return_value = (stdout, result_mock)       # 
               
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                valid = Gitter.validate_gh_version()
                
        # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"gh version 2.54.0 is not supported. Please upgrade to version {Gitter.reguired_version} or higher", mock_stderr.getvalue())           

    @pytest.mark.unittest
    @patch('gitter.Gitter.run',new_callable=AsyncMock)
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
    @patch('gitter.Gitter.run',new_callable=AsyncMock)
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
    @patch('gitter.Gitter.run',new_callable=AsyncMock)
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
    @patch('subprocess.run')
    def test_run_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = Mock(
            stdout='fa05229e20052cbb1a13d0c6ee9da7115df55b89',
            stderr='',
            returncode=0
        )
    
        gitter = Gitter(cmd="git rev-parse HEAD", msg="Get current commit hash")
        [value,result] = asyncio.run(gitter.run())                              
        self.assertEqual(value, 'fa05229e20052cbb1a13d0c6ee9da7115df55b89')
        mock_subprocess_run.assert_called_once()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(gitter.get('msg'), "Get current commit hash")
        self.assertEqual(gitter.get('cmd'), "git rev-parse HEAD")
        