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

from issue import Issue
from devbranch import Devbranch

class TestIssue(unittest.TestCase):

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_constructor_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
        ]
               
        issue = Issue(number='17')

        # Assertions
        self.assertEqual(issue.get('number'), '17')
        self.assertEqual(issue.get('url'), 'https://github.com/thetechcollective/gh-tt/issues/17')
        self.assertEqual(issue.get('title'), "Add a 'deliver' subcommand")

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_constructor_bad_issue(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["", Mock(returncode=1, stderr='ERROR', stdout='')],  # Get the url and title from the issue
        ]
               
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                issue = Issue(number=17)

       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Issue '17' doesn't exit in current git context", mock_stderr.getvalue())
    
    
    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_constructor_bad_json(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["Not valid JSON", Mock(returncode=0, stderr='ERROR', stdout='')],  # Get the url and title from the issue
        ]
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                issue = Issue(number=17)
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Could not get the issue url or title on issue number: '17", mock_stderr.getvalue())
        

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_constructor_incomplete_json(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['{\n  "Nothing":"Nope"\n}', Mock(returncode=0, stderr='ERROR', stdout='')],  # Get the url and title from the issue
        ]
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                issue = Issue(number=17)
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Could not get the issue url or title from incomplete JSON", mock_stderr.getvalue())        

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_create_issue_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""
             
Creating issue in thetechcollective/gh-tt

https://github.com/thetechcollective/gh-tt/issues/17
             """, Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            
        ]
        
        issue = Issue.create_new(title="Add a 'deliver' subcommand")
        
        # Assertions
        self.assertEqual(issue.get('url'), 'https://github.com/thetechcollective/gh-tt/issues/17')
        self.assertEqual(issue.get('title'), "Add a 'deliver' subcommand")
        self.assertEqual(issue.get('number'), '17')

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_create_issue_nu_invalid_url(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["not a valid url", Mock(returncode=0, stderr='1', stdout='')],  # Get the url and title from the issue  
        ]
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                issue = Issue.create_new(title="Add a 'deliver' subcommand")
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Could not capture the issue URL from the output", mock_stderr.getvalue())        

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_add_to_project_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ['PVTI_lAHOAAJfZM4AxVEKzgXi48Q', Mock(returncode=0, stderr='', stdout='')], # Add the issue to the project
        ]
               
        issue = Issue(number='17')
        item_id = issue.add_to_project(owner='lakruzz', number='12')

        # Assertions
        self.assertEqual(item_id, 'PVTI_lAHOAAJfZM4AxVEKzgXi48Q')

    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_add_to_project_failure(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ['', Mock(returncode=1, stderr='Error', stdout='')], # Add the issue to the project
        ]
               
        issue = Issue(number='17')

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                item_id = issue.add_to_project(owner='lakruzz', number='12')
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Could not add the issue to the project lakruzz/1", mock_stderr.getvalue())     
        
    @pytest.mark.unittest
    @patch('issue.Gitter')
    def test_issue_assign_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue        
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')],  # Assign the issue
        ]
        
        issue = Issue(number=17)
        issue.assign(assignee='@me')
        
        # Assertions
        self.assertEqual(issue.get('assignee'), '@me')
