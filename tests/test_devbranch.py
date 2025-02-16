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
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test_constructor_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)], # git fetch
            ['main', None], # gh repo view defaultBranchRef
            ['origin', None], # git remote
            ['17-Add_a_deliver_subcommand', None], # git branch
            
        ]

        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]  

        devbranch = Devbranch()
        self.assertEqual(devbranch.props['default_branch'], 'main')
        self.assertEqual(devbranch.props['remote'], 'origin')
        
    @pytest.mark.unittest
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test__get_branch_sha1_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['9cc26a27febb99af5785150e40b6821fa00e8c9a', Mock(returncode=0, stderr='', stdout='')], # Get the SHA1 of the current branch
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]  
                
        devbranch = Devbranch()
        key = 'SHA1'
        value = devbranch._Devbranch__get_branch_sha1() # 1st time run the command
        value = devbranch._Devbranch__get_branch_sha1() # 2nd time get the value from the class props
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test__get_merge_base_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['6aa5faf9fb4a0d650dd7becc1588fed5770c2fda', Mock(returncode=0, stderr='', stdout='')], # Get the SHA1 of the current branch
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]  
        devbranch = Devbranch()
        key = 'merge_base'
        value = devbranch._Devbranch__get_merge_base() # 1st time run the command
        value = devbranch._Devbranch__get_merge_base() # 2nd time get the value from the class props
        self.assertEqual(value, '6aa5faf9fb4a0d650dd7becc1588fed5770c2fda')
        self.assertEqual(devbranch.get(key), value)

    @pytest.mark.unittest
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test__get_commit_count_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ['2', Mock(returncode=0, stderr='', stdout='')], # Get the commit count
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]        
        
        devbranch = Devbranch()
        key = 'commit_count'
        value = devbranch._Devbranch__get_commit_count() # 1st time run the command
        value = devbranch._Devbranch__get_commit_count() # 2nd time get the value from the class props
        self.assertEqual(value, '2')
        self.assertEqual(devbranch.get(key), value)
        
    @pytest.mark.unittest
    @patch('issue.Gitter')
    @patch('devbranch.Gitter')
    def test__get_commit_message_success(self, MockDevbranchGitter, MockIssueGitter):
        # Setup
        mock_gitter_instance = MockDevbranchGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=0)],             # git fetch
            ['main', None],                       # gh repo view defaultBranchRef
            ['origin', None],                     # git remote
            ['17-Add_a_deliver_subcommand',None], # git branch
            ["related to Add a 'deliver' subcommand #17", Mock(returncode=0, stderr='', stdout='')], # Get the commit message
        ]
        
        mock_gitter_instance = MockIssueGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['https://github.com/thetechcollective/gh-tt/issues/17', Mock(returncode=0, stderr='', stdout='')], #Get the url from the issue
            ["Add a 'deliver' subcommand", Mock(returncode=0, stderr='', stdout='')], #Get the title of the issue
        ]        
        
        devbranch = Devbranch()
        key = 'commit_message'
        value = devbranch._Devbranch__get_commit_message() # 1st time run the command
        value = devbranch._Devbranch__get_commit_message() # 2nd time get the value from the class props
        self.assertEqual(value, "related to Add a 'deliver' subcommand #17")
        self.assertEqual(devbranch.get(key), value)

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
                             mock_check_rebase):
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
