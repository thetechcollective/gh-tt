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

from devbranch import Devbranch
from gitter import Gitter

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
    def test_constructor_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand', None], # git branch   
        ]

        devbranch = Devbranch()
        self.assertEqual(devbranch.get('default_branch'), 'main')
        self.assertEqual(devbranch.get('remote'), 'origin')
        self.assertEqual(devbranch.get('branch_name'), '17-Add_a_deliver_subcommand')
        self.assertEqual(devbranch.get('issue_number'), '17')
        self.assertEqual(devbranch.get('sha1'), None)
        
    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test_constructor_success_no_issue(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['Not-an-issue-Add_a_deliver_subcommand', None], # git branch   
        ]

        devbranch = Devbranch()
        self.assertEqual(devbranch.get('default_branch'), 'main')
        self.assertEqual(devbranch.get('remote'), 'origin')
        self.assertEqual(devbranch.get('branch_name'), 'Not-an-issue-Add_a_deliver_subcommand')
        self.assertEqual(devbranch.get('issue_number'), None)
        self.assertEqual(devbranch.get('sha1'), None)       
        
        
        
    ## TODO    
    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test__get_branch_sha1_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['9cc26a27febb99af5785150e40b6821fa00e8c9a', Mock(returncode=0, stderr='', stdout='')], # Get the SHA1 of the current branch
        ]
                        
        devbranch = Devbranch()
        key = 'sha1'
        value = devbranch._Devbranch__get_branch_sha1() # 1st time run the command
        value = devbranch._Devbranch__get_branch_sha1() # 2nd time get the value from the class props
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test__get_merge_base_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['6aa5faf9fb4a0d650dd7becc1588fed5770c2fda', Mock(returncode=0, stderr='', stdout='')], # Get the SHA1 of the current branch
        ]
        
        devbranch = Devbranch()
        key = 'merge_base'
        value = devbranch._Devbranch__get_merge_base() # 1st time run the command
        value = devbranch._Devbranch__get_merge_base() # 2nd time get the value from the class props
        self.assertEqual(value, '6aa5faf9fb4a0d650dd7becc1588fed5770c2fda')
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test__get_commit_count_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['2', Mock(returncode=0, stderr='', stdout='')], # Get the commit count
        ]         
        
        devbranch = Devbranch()
        key = 'commit_count'
        value = devbranch._Devbranch__get_commit_count() # 1st time run the command
        value = devbranch._Devbranch__get_commit_count() # 2nd time get the value from the class props
        self.assertEqual(value, '2')
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test__check_rebase_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['e5f2dc1389414523fa20f54c819841d9f360114d', Mock(returncode=0, stderr='', stdout='')], # Get the commit count
        ]         
        
        devbranch = Devbranch()
        

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            devbranch._Devbranch__check_rebase()
       # Assertions
        self.assertIn("WARNING:\nThe main branch has commits your branch has never seen. A rebase is required. Do it now!", mock_stdout.getvalue()) 
       
    @pytest.mark.unittest
    @patch('devbranch.Gitter')
    def test__get_commit_message_success(self, MockDevbranchGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ["related to Add a 'deliver' subcommand #17", Mock(returncode=0, stderr='', stdout='')], # Get the commit message
        ]      
        
        devbranch = Devbranch()
        key = 'commit_message'
        value = devbranch._Devbranch__get_commit_message() # 1st time run the command
        value = devbranch._Devbranch__get_commit_message() # 2nd time get the value from the class props
        self.assertEqual(value, "related to Add a 'deliver' subcommand #17")
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('project.Gitter')
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test_set_issue_reuse_local_success(self, MockDevbranchGitter, MockIssueGitter, MockProjectGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ["""
17-Add_a_deliver_subcommand
26-Refactor
7-Add_unit_tests
main
             """, Mock(returncode=0, stderr='', stdout='')], # Get all local branches
            ["""
Switched to branch '17-Add_a_deliver_subcommand'
Your branch is up to date with 'origin/17-Add_a_deliver_subcommand'.
             """, Mock(returncode=0, stderr='', stdout='')],  # Switch to the branch ...}           
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')], # Assign @me to the issue
        ]     
        
        mock_gitter_instance = MockProjectGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gitsquash_lab/testbed', Mock(returncode=0, stderr='', stdout='/home/vscode/gh-tt\n')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            # get_project_deliver_field:value
            ['Status:Pull Request Created', None],
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description     
            ['Edited item "Add a \'deliver\' subcommand"', None],  # update_field 

        ]               
              
        
        devbranch = Devbranch()
        devbranch.set_issue(issue_number='17', assign=True)
        self.assertEqual(devbranch.get('issue_number'), "17")

    @pytest.mark.unittest
    @patch('project.Gitter')
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test_set_issue_create_new_branch_success(self, MockDevbranchGitter, MockIssueGitter, MockProjectGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ["""
26-Refactor
7-Add_unit_tests
main
             """, Mock(returncode=0, stderr='', stdout='')], # Get all local branches
            ["""
origin/14-remote_is_not_a_valid_key
origin/26-Refactor
origin/27-Refactor
origin/7-Add_unit_tests
origin
origin/main            
             """, Mock(returncode=0, stderr='', stdout='')], # Get all remote branches            
            ["""
github.com/thetechcollective/gh-tt/tree/15-Some_title
From https://thetechcollective/gh-tt
 * [new branch]      15-Some_title -> origin/15-Some_title
             """, Mock(returncode=0, stderr='', stdout='')],  # Switch to the branch ...}           
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')], # Assign @me to the issue
        ]     
        
        mock_gitter_instance = MockProjectGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['git rev-parse --show-toplevel', Mock(returncode=0, stderr='', stdout='/home/vscode/gh-tt\n')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            # get_project_deliver_field:value
            ['Status:Pull Request Created', None],
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description     
            ['Edited item "Add a \'deliver\' subcommand"', None],  # update_field 
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
              "id": "PVTF_lAHOAAJfZM4AxVEKzgoxKtQ",
              "name": "Start",
              "type": "ProjectV2Field"
            }), None],                  # get_field_description     
            ['Edited item "Add a \'deliver\' subcommand"', None]  # update_field 
        ]               
              
        
        devbranch = Devbranch()
        devbranch.set_issue(issue_number='17', assign=True)
        self.assertEqual(devbranch.get('issue_number'), "17")
        
    @pytest.mark.unittest
    @patch('project.Gitter')
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test_set_issue_reuse_remote_success(self, MockDevbranchGitter, MockIssueGitter, MockProjectGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ["""
26-Refactor
7-Add_unit_tests
main
             """, Mock(returncode=0, stderr='', stdout='')], # Get all local branches
            ["""
origin/14-remote_is_not_a_valid_key
origin/17-Add_a_deliver_subcommand
origin/26-Refactor
origin/27-Refactor
origin/7-Add_unit_tests
origin
origin/main            
             """, Mock(returncode=0, stderr='', stdout='')], # Get all remote branches            
            ["""
Switched to branch '17-Add_a_deliver_subcommand'
Your branch is up to date with 'origin/17-Add_a_deliver_subcommand'.
             """, Mock(returncode=0, stderr='', stdout='')],  # Switch to the branch ...}           
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["""{
                  "title": "Add a 'deliver' subcommand",
                  "url": "https://github.com/thetechcollective/gh-tt/issues/17"
                }""", Mock(returncode=0, stderr='', stdout='')],  # Get the url and title from the issue
            ["https://github.com/thetechcollective/gh-tt/issues/17", Mock(returncode=0, stderr='', stdout='')], # Assign @me to the issue
        ]     
        
        mock_gitter_instance = MockProjectGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['git rev-parse --show-toplevel', Mock(returncode=0, stderr='', stdout='/home/vscode/gh-tt\n')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            # get_project_deliver_field:value
            ['Status:Pull Request Created', None],
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description     
            ['Edited item "Add a \'deliver\' subcommand"', None]  # update_field 
        ]               
              
        
        devbranch = Devbranch()
        devbranch.set_issue(issue_number='17', assign=True)
        self.assertEqual(devbranch.get('issue_number'), "17")
   

    @pytest.mark.unittest
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test__squeeze_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['6aa5faf9fb4a0d650dd7becc1588fed5770c2fda', Mock(returncode=0, stderr='', stdout='')], # Get the merge base 
            ["related to Add a 'deliver' subcommand #17", Mock(returncode=0, stderr='', stdout='')], # Get commit message           
            ["de291d6f38de30e8037142d6bb2afb5d69429368", Mock(returncode=0, stderr='', stdout='')], # Squeeze the commits
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]        
        
        devbranch = Devbranch()
        key = 'squeeze_sha1'
        value = devbranch._Devbranch__squeeze() # 1st time run the command - this functions doesn't have a cache
        self.assertEqual(value, "de291d6f38de30e8037142d6bb2afb5d69429368")
        self.assertEqual(devbranch.get(key), value)
    
        
    @pytest.mark.unittest
    @patch('devbranch.Devbranch._Devbranch__get_branch_sha1', return_value='9cc26a27febb99af5785150e40b6821fa00e8c9a')
    @patch('devbranch.Devbranch._Devbranch__get_merge_base', return_value='6aa5faf9fb4a0d650dd7becc1588fed5770c2fda')
    @patch('devbranch.Devbranch._Devbranch__get_commit_count', return_value='2')
    @patch('devbranch.Devbranch._Devbranch__get_commit_message', return_value="related to Add a 'deliver' subcommand #17")
    @patch('devbranch.Devbranch._Devbranch__validate_commit_message', return_value="related to Add a 'deliver' subcommand #17 - close #17")
    @patch('devbranch.Devbranch._Devbranch__squeeze', return_value='de291d6f38de30e8037142d6bb2afb5d69429368')
    @patch('devbranch.Devbranch._Devbranch__compare_before_after_trees', return_value=True) 
    @patch('devbranch.Devbranch._Devbranch__reset_branch', return_value='de291d6f38de30e8037142d6bb2afb5d69429368')     
    @patch('devbranch.Devbranch._Devbranch__check_rebase', return_value=True)     
    @patch('devbranch.Devbranch._Devbranch__workspace_is_clean', return_value=True)     
    @patch('devbranch.Devbranch._Devbranch__rebase', return_value=True)   
    @patch('devbranch.Devbranch._Devbranch__push', return_value=True)  
    @patch('devbranch.Gitter')
    def test_collaps_success(self, MockGitter, 
                             mock_get_branch_sha1, 
                             mock_get_merge_base, 
                             mock_get_commit_count,
                             mock_get_commit_message,
                             mock_validate_commit_message,
                             mock_squeeze,
                             mock_compare_before_after_tree,
                             mock_reset_branch,
                             mock_check_rebase,
                             mock_workspace_is_clean,
                             mock_rebase,
                             mock_push):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]

        devbranch = Devbranch()
        devbranch.collapse()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')
        
    @pytest.mark.unittest
    @patch('devbranch.Devbranch._Devbranch__get_branch_sha1', return_value='9cc26a27febb99af5785150e40b6821fa00e8c9a')
    @patch('devbranch.Devbranch._Devbranch__get_merge_base', return_value='6aa5faf9fb4a0d650dd7becc1588fed5770c2fda')
    @patch('devbranch.Devbranch._Devbranch__get_commit_count', return_value='2')
    @patch('devbranch.Devbranch._Devbranch__get_commit_message', return_value="related to Add a 'deliver' subcommand #17")
    @patch('devbranch.Devbranch._Devbranch__validate_commit_message', return_value="related to Add a 'deliver' subcommand #17 - close #17")
    @patch('devbranch.Devbranch._Devbranch__squeeze', return_value='de291d6f38de30e8037142d6bb2afb5d69429368')
    @patch('devbranch.Devbranch._Devbranch__compare_before_after_trees', return_value=True) 
    @patch('devbranch.Devbranch._Devbranch__reset_branch', return_value='de291d6f38de30e8037142d6bb2afb5d69429368')     
    @patch('devbranch.Devbranch._Devbranch__check_rebase', return_value=True)     
    @patch('devbranch.Gitter')
    def test_collaps_on_main_failure(self, MockGitter, 
                             mock_get_branch_sha1, 
                             mock_get_merge_base, 
                             mock_get_commit_count,
                             mock_get_commit_message,
                             mock_validate_commit_message,
                             mock_squeeze,
                             mock_compare_before_after_tree,
                             mock_reset_branch,
                             mock_check_rebase):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['main',None], # git branch
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]

        devbranch = Devbranch()        
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                devbranch.collapse()
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR: Cannot collapse the default branch: (main)\nSwitch to a development branch", mock_stderr.getvalue())            
        

#    @pytest.mark.unittest
#    @patch('devbranch.Gitter')
#    def test_deliver_success(self, MockGitter):
#        # Setup
#        mock_gitter_instance = MockGitter.return_value
#        mock_gitter_instance.run.side_effect = [
#            ['', Mock(returncode=0)], # git fetch
#            ['main', None], # gh repo view defaultBranchRef
#            ['origin', None], # git remote
#            ['17-Add_a_deliver_subcommand',None], # git branch
#            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
#            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
#        ]
#
#        devbranch = Devbranch()
#        devbranch.deliver()
#        self.assertEqual(devbranch.props['default_branch'], 'main')
#        self.assertEqual(devbranch.props['remote'], 'origin')

if __name__ == '__main__':
    unittest.main()
