import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from gitter import Gitter


class TestGitter(unittest.TestCase):

    @pytest.mark.unittest
    @patch('gitter.Gitter')
    def test_gitter_validate_gh_version_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0", Mock(returncode=0, stderr="")],            
        ]
               
        valid = Gitter.validate_gh_version()
        self.assertTrue(valid)

    @pytest.mark.unittest
    @patch('gitter.Gitter')
    def test_gitter_validate_gh_version_failure(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["gh version 2.54.0 (2024-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.54.0", Mock(returncode=0, stderr="")],             
        ]
               
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                valid = Gitter.validate_gh_version()
                
        # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"gh version 2.54.0 is not supported. Please upgrade to version {Gitter.reguired_version} or higher", mock_stderr.getvalue())           

    @pytest.mark.unittest
    @patch('gitter.Gitter')
    def test_gitter_validate_gh_scope_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""github.com
  ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'project', 'workflow'""", Mock(returncode=0, stderr="")]              
        ]
               
        valid = Gitter.validate_gh_scope(scope="project")
        self.assertTrue(valid)
        
    @pytest.mark.unittest
    @patch('gitter.Gitter')
    def test_gitter_validate_gh_scope_failure(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""github.com
  ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'read:project', 'workflow'""", Mock(returncode=0, stderr="")]              
        ]
        value="project"       
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                valid = Gitter.validate_gh_scope(scope=value)
                              
        # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"gh token does not have the required scope '{value}'", mock_stderr.getvalue())  
