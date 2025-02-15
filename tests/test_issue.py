import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from issue import Issue
from devbranch import Devbranch

class TestIssue(unittest.TestCase):

    @pytest.mark.unittest
    @patch('issue.Devbranch', autospec=True)
    @patch('issue.Gitter')
    def test_issue_constructor_success(self, MockGitter, MockDevbranch):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')],  # Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')],  # Get the title of the issue
        ]
        
        # Mock a healthy Devbranch object
        mock_devbranch_instance = MockDevbranch.return_value
        mock_devbranch_instance.props = {
            'workdir': '/workspaces/gh-tt',
            'verbose': False,
            'default_branch': 'main',
            'remote': 'origin',
            'branch_name': '17-Add_a_deliver_subcommand'}
        
        issue = Issue(devbranch=mock_devbranch_instance)

        # Assertions
        self.assertEqual(issue.get('number'), '17')
        self.assertEqual(issue.get('url'), 'https://github.com/thetechcollective/gh-tt/issues/17')
        self.assertEqual(issue.get('title'), "Add a 'deliver' subcommand")

    @pytest.mark.unittest
    @patch('issue.Devbranch', autospec=True)
    @patch('issue.Gitter')
    def test_issue_constructor_bad_branch_name(self, MockGitter, MockDevbranch):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')],  # Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')],  # Get the title of the issue
        ]
        
        # Mock a healthy Devbranch object
        mock_devbranch_instance = MockDevbranch.return_value
        mock_devbranch_instance.props = {
            'workdir': '/workspaces/gh-tt',
            'default_branch': 'main',
            'remote': 'origin',
            'branch_name': 'notanumber-Add_a_deliver_subcommand'}
        
        with self.assertRaises(ValueError) as e:
            issue = Issue(devbranch=mock_devbranch_instance)
        self.assertRegex(str(e.exception), r"Branch name notanumber-Add_a_deliver_subcommand does not contain an issue number")     

    @pytest.mark.unittest
    @patch('issue.Devbranch', autospec=True)
    @patch('issue.Gitter')
    def test_issue_constructor_bad_url(self, MockGitter, MockDevbranch):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["", Mock(returncode=1, stderr='ERROR:The Error', stdout='')],  # Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')],  # Get the title of the issue
        ]
        
        # Mock a healthy Devbranch object
        mock_devbranch_instance = MockDevbranch.return_value
        mock_devbranch_instance.props = {
            'workdir': '/workspaces/gh-tt',
            'default_branch': 'main',
            'remote': 'origin',
            'branch_name': '17-Add_a_deliver_subcommand'}
        
        with self.assertRaises(ValueError) as e:
            issue = Issue(devbranch=mock_devbranch_instance)
        self.assertRegex(str(e.exception), r"Could not get the issue url on issue number: '17'.*")     

    @pytest.mark.unittest
    @patch('issue.Devbranch', autospec=True)
    @patch('issue.Gitter')
    def test_issue_constructor_bad_title(self, MockGitter, MockDevbranch):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')],  # Get the url from the issue
            ["", Mock(returncode=1, stderr='ERROR:The Error', stdout='')],  # Get the title of the issue
        ]
        
        # Mock a healthy Devbranch object
        mock_devbranch_instance = MockDevbranch.return_value
        mock_devbranch_instance.props = {
            'workdir': '/workspaces/gh-tt',
            'verbose': False,
            'default_branch': 'main',
            'remote': 'origin',
            'branch_name': '17-Add_a_deliver_subcommand'}
        
        with self.assertRaises(ValueError) as e:
            issue = Issue(devbranch=mock_devbranch_instance)
        self.assertRegex(str(e.exception), r"Could not find title on issue number: '17'.*") 
        
    @pytest.mark.unittest
    @patch('issue.Devbranch', autospec=True)
    @patch('issue.Gitter')
    def test_issue_constructor_new_workdir(self, MockGitter, MockDevbranch):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')],  # Get the url from the issue
            ["", Mock(returncode=1, stderr='ERROR:The Error', stdout='')],  # Get the title of the issue
        ]
        
        # Mock a healthy Devbranch object
        mock_devbranch_instance = MockDevbranch.return_value
        mock_devbranch_instance.props = {
            'workdir': '/workspaces/gh-tt',
            'default_branch': 'main',
            'verbose': False,
            'remote': 'origin',
            'branch_name': '17-Add_a_deliver_subcommand'}
        
        with self.assertRaises(ValueError) as e:
            issue = Issue(devbranch=mock_devbranch_instance)
        self.assertRegex(str(e.exception), r"Could not find title on issue number: '17'.*") 