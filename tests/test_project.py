import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from project import Project


class TestProject(unittest.TestCase):

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_success(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField', 
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description
            ['Edited item "another new issue"', None]                  # update_field
        ]

        project = Project(owner="lakruzz", number="13")
        result = project.update_field(
            owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7", field="Status", field_value="In Progress")

        # Assertions
        self.assertRegex(result, r"Edited item \".+\"")
        mock_gitter_instance.run.assert_called_with(cache=False)

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_success_impicit_owner_number(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField', 
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description
            ['Edited item "another new issue"', None]                  # update_field
        ]

        project = Project(owner="lakruzz", number="13")
        result = project.update_field(url="https://github.com/lakruzz/gitsquash_lab/issues/7", field="Status", field_value="In Progress") # Owner and number are optional - here they are omitted

        # Assertions
        self.assertRegex(result, r"Edited item \".+\"")
        mock_gitter_instance.run.assert_called_with(cache=False)

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_option_not_found(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType', # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number=13, url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="Blaha") # Bad field_value

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_type_not_supported(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType', # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="In Progress")

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_descriptor_is_empty(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({}), Mock(returncode=0, stderr="")]                  # get_field_description empty return value
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError) as e:
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="In Progress")
        self.assertRegex(str(e.exception), r"Field Status not found in project")
            
    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_field_not_found(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType', # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress") # bad field name

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_field_id_not_found(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'blaha': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI', #id field not found
                'type': 'ProjectV2SingleSelectField', 
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}] 
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress") # bad field name

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_update_field_field_type_not_found(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI', 
                'blaha': 'ProjectV2SingleSelectField', #id field not found
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}] 
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress") # bad field name
        
                
    @pytest.mark.unittest
    @patch.object(Project, '__init__', lambda self, owner, number: None)
    @patch('project.Gitter')
    def test_validate_gh_access_invalid_version(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["gh version 2.54.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.54.0", Mock(returncode=0, stderr="")]  
        ]

        project = Project(owner="lakruzz", number="13")
        [validated, msg] = project.validate_gh_access()
        self.assertFalse(validated)
        self.assertRegex(msg, r"gh version 2.54.0 is not supported. Please upgrade to version 2.55.0 or higher") 

    @pytest.mark.unittest
    @patch('project.Gitter')
    @patch.object(Project, '__init__', lambda self, owner, number: None)
    def test_validate_gh_access_invalid_scope(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0", Mock(returncode=0, stderr="")],
            ["""github.com
  ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'""", Mock(returncode=0, stderr="")]              
        ]

        project = Project(owner="lakruzz", number="13")
        [validated, msg] = project.validate_gh_access()
        self.assertFalse(validated)
        self.assertRegex(msg, r"gh token does not have the required scope") 

    @pytest.mark.unittest
    @patch.object(Project, '__init__', lambda self, owner, number: None)
    @patch('project.Gitter')
    def test_validate_gh_access_valid(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["gh version 2.65.0 (2025-01-06)\nhttps://github.com/cli/cli/releases/tag/v2.65.0", Mock(returncode=0, stderr="")],
            ["""github.com
  ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'project', 'repo', 'workflow'""", Mock(returncode=0, stderr="")]              
        ]

        project = Project(owner="lakruzz", number="13")
        [validated, msg] = project.validate_gh_access()
        self.assertTrue(validated)

    @pytest.mark.unittest
    def test_project_constructor_invalid_workdir_found(self):
        with self.assertRaises(FileNotFoundError):
            project = Project(owner="lakruzz", number="13", workdir="blaha_obscure_dir")


    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[False, ''])
    @patch('project.Gitter')
    def test_project_constructor_invalid_gh_access(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = []
        
        with self.assertRaises(RuntimeError) as e:
            project = Project(owner="lakruzz", number="13", workdir=".")
        self.assertRegex(str(e.exception), r"WARNING\nYour GH CLI is not setup correctly:.*")


    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_valid_workdir_found(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = []

        project = Project(owner="lakruzz", number="13", workdir=".")
        self.assertEqual(project.props['project_owner'], "lakruzz")
        self.assertEqual(project.props['project_number'], "13")
        
    @pytest.mark.unittest
    @patch('subprocess.run')
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_invalid_gitroot(self, MockGitter, MockValidateGhAccess, MockSubprocessRun):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = []

        # Mock subprocess.run to return an empty result
        MockSubprocessRun.return_value = Mock(stdout='', stderr='', returncode=1)

        with self.assertRaises(FileNotFoundError) as e:
            project = Project()
        self.assertRegex(str(e.exception), r"Could not determine the git root directory")

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_read_config_success(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None] # get_project_deliver_field:value    
        ]

        project = Project()
        self.assertEqual(project.props['project_owner'], "lakruzz")
        self.assertEqual(project.props['project_number'], "13")
        self.assertEqual(project.props['workon_field'], "Status")
        self.assertEqual(project.props['workon_field_value'], "In Progress")
        
    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_owner(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception), r"Project owner not found in the git config")

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_project_number(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['lakruzz', None],  # get_project_owner
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception), r"Project number not found in the git config")

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_workon_trigger(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
            ['Status:Pull Request Created', None]  # # get_project_deliver_field:value    

        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception), r"Failed to read workon_field and workon_field_value from the .gitconfig")

    @pytest.mark.unittest
    @patch.object(Project, 'validate_gh_access', return_value=[True, ''])
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_deliver_trigger(self, MockGitter, MockValidateGhAccess):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value            
            ['', Mock(return_value=1, stderr='Error')],  # get_project_deliver_field:value    

        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception), r"Failed to read deliver_field and deliver_field_value from the .gitconfig")

        
if __name__ == '__main__':
    unittest.main()
