import unittest
import os
import sys
import json
from io import StringIO
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from unittest.mock import AsyncMock
import pytest
import asyncio

# fmt: off
class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from config import Config
from gitter import Gitter
from devbranch import Devbranch
# fmt: on


class TestDevbranch(unittest.TestCase):

    @pytest.mark.unittest
    def test_constructor_success(self):
        devbranch = Devbranch()
        self.assertEqual(devbranch.get('unstaged_changes'), None)
        self.assertEqual(devbranch.get('staged_changes'), None)
        self.assertEqual(devbranch.get('is_dirty'), None)
        self.assertEqual(devbranch.get('issue_number'), None)
        self.assertEqual(devbranch._manifest_loaded, True)

    @pytest.mark.unittest
    def test_load_issue_number_success(self):
        devbranch = Devbranch().from_json(
            file='tests/data/devbranch/.tt-config-set_issue.json')
        asyncio.run(devbranch._load_issue_number())
        self.assertEqual(devbranch.get('issue_number'), '95')

    @pytest.mark.unittest
    def test_load_issue_number_none(self):
        devbranch = Devbranch().from_json(file='tests/data/devbranch/main.json')
        asyncio.run(devbranch._load_issue_number())
        self.assertEqual(devbranch.get('issue_number'), None)
        self.assertEqual(devbranch.get('branch_name'), 'main')

    @pytest.mark.unittest
    @patch('devbranch.Devbranch._run', new_callable=AsyncMock)
    def test__reuse_issue_branch(self, mock_run):
        mock_run.return_value = ""

        Gitter.verbose = True
        # Load the recorded instance of Devbranch
        devbranch = Devbranch().from_json(
            file='tests/data/devbranch/workon_reuse_issue_branch.json')

        # Create a single loop for all test cases
        loop = asyncio.new_event_loop()
        reuse_local = loop.run_until_complete(
            devbranch._Devbranch__reuse_issue_branch(7))
        self.assertTrue(reuse_local)
        mock_run.assert_called_once_with('checkout_local_branch')
        mock_run.reset_mock()

        devbranch.props['local_branches'] = ""
        reuse_remote = loop.run_until_complete(
            devbranch._Devbranch__reuse_issue_branch(7))
        self.assertTrue(reuse_remote)
        mock_run.assert_called_once_with('checkout_remote_branch')
        mock_run.reset_mock()  # Reset the mock for the next call

        devbranch.props['remote_branches'] = ""
        reuse = loop.run_until_complete(
            devbranch._Devbranch__reuse_issue_branch(7))
        self.assertFalse(reuse)
        loop.close()

    @pytest.mark.unittest
    @patch('devbranch.Devbranch._run', new_callable=AsyncMock)
    @patch('sys.stderr', new_callable=StringIO)
    def test__compare_before_after_trees(self, mock_stderr, mock_run):
        mock_run.side_effect = [
            "",             # no diffs
            "somefile.txt"  # Some diffs
        ]

        Gitter.verbose = True
        # Load the recorded instance of Devbranch
        devbranch = Devbranch().from_json(
            file='tests/data/devbranch/devbranch-squeeze.json')

        # Create a single loop for all test cases
        loop = asyncio.new_event_loop()
        # no diffs
        diff = loop.run_until_complete(
            devbranch._Devbranch__compare_before_after_trees())
        self.assertTrue(diff)
        mock_run.assert_called_once_with('compare_trees')
        mock_run.reset_mock()

        # Some diffs
        with self.assertRaises(SystemExit) as cm:
            diff = loop.run_until_complete(
                devbranch._Devbranch__compare_before_after_trees())
            
        self.assertEqual(cm.exception.code, 1)
        self.assertRegex(mock_stderr.getvalue(), r"FATAL:\nThe squeezed commit tree (.*) is not identical to the one on the issue branch" )
        mock_run.assert_called_once_with('compare_trees')
        mock_run.reset_mock()


        loop.close()

    @pytest.mark.unittest
    def test__load_squeezed_commit_message(self):

        Gitter.verbose = True
        # Load the recorded instance of Devbranch
        devbranch = Devbranch().from_json(
            file='tests/data/devbranch/devbranch-squeeze.json')

        # Create a single loop for all test cases
        loop = asyncio.new_event_loop()
        # no diffs
        message = loop.run_until_complete(
            devbranch._Devbranch__load_squeezed_commit_message())
        self.assertRegex(
            message,
            r"^Add support for .*ready.*resolves #91"
        )
        self.assertRegex(
            message,
            r".*a201d0f.*"
        )

        loop.close()

    @pytest.mark.unittest
    @patch('devbranch.Devbranch._force_prop_reload', new_callable=AsyncMock)
    def test_load_status(self, mock_force_prop_reload):
        mock_force_prop_reload.return_value = None

        Gitter.verbose = True
        # Load the recorded instance of Devbranch
        devbranch = Devbranch().from_json(
            file='tests/data/devbranch/devbranch-squeeze.json')

        # Create a single loop for all test cases
        loop = asyncio.new_event_loop()
        # no diffs

        self.assertEqual(devbranch.get('unstaged_changes'), None)
        self.assertEqual(devbranch.get('staged_changes'), None)
        self.assertEqual(devbranch.get('is_dirty'), None)

        loop.run_until_complete(
            devbranch._load_status())
        
        self.assertTrue(devbranch.get('is_dirty'))

        self.assertIn("MM .github/workflows/python-app.yml", devbranch.get('staged_changes'))
        self.assertIn("M  gh_tt.py", devbranch.get('staged_changes'))

        self.assertIn(" M classes/gitter.py", devbranch.get('unstaged_changes'))
        self.assertIn("?? tests/test_config.py", devbranch.get('unstaged_changes'))

        # Run again, to check if it is cached (nothing is change but used to get coverage on the retun-when-already-loaded branch)
        loop.run_until_complete(
            devbranch._load_status())
        
        loop.run_until_complete(
            devbranch._load_status(reload=True))
        mock_force_prop_reload.assert_called_once_with('status')
        
  

        loop.close()



if __name__ == '__main__':
    unittest.main()
