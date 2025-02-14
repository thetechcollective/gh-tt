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
    def test_set_issue_fail(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
        ]

        devbranch = Devbranch()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')


if __name__ == '__main__':
    unittest.main()
