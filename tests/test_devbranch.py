import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from devbranch import Devbranch

class TestDevbranch(unittest.TestCase):

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test_failed_fetch(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=1, stderr="Error message")] # git fetch
        ]
        with self.assertRaises(RuntimeError) as e:
            devbranch = Devbranch()
        self.assertRegex(str(e.exception), r"Error: Unable to fetch from the remote")            

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test_constructor_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
        ]

        devbranch = Devbranch()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test_constructor_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
        ]

        devbranch = Devbranch()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')

    @pytest.mark.unittest
    @patch('devbranch.Devbranch._Devbranch__get_branch_sha1', return_value='9cc26a27febb99af5785150e40b6821fa00e8c9a')
    @patch('devbranch.Devbranch._Devbranch__get_merge_base', return_value='6aa5faf9fb4a0d650dd7becc1588fed5770c2fda')
    @patch('devbranch.Devbranch._Devbranch__get_commit_count', return_value='2')
    @patch('devbranch.Devbranch._Devbranch__get_commit_message', return_value="related to Add a 'deliver' subcommand #17")
    @patch('devbranch.Devbranch._Devbranch__validate_commit_message', return_value=True)
    @patch('devbranch.Gitter')
    def test_collaps_success(self, MockGitter, 
                             mock_get_branch_sha1, 
                             mock_get_merge_base, 
                             mock_get_commit_count,
                             mock_get_commit_message,
                             mock_validate_commit_message):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
        ]

        devbranch = Devbranch()
        devbranch.collapse()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test_deliver_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
        ]

        devbranch = Devbranch()
        devbranch.deliver()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')

if __name__ == '__main__':
    unittest.main()
