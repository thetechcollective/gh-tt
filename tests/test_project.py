import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest
from io import StringIO

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from project import Project

class TestProject(unittest.TestCase):


    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description
            ['Edited item "another new issue"',
                None]                  # update_field
        ]

        project = Project(owner="lakruzz", number="13")
        result = project.update_field(
            owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7", field="Status", field_value="In Progress")

        # Assertions
        self.assertRegex(result, r"Edited item \".+\"")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_success_impicit_owner_number(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value 
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description
            ['Edited item "another new issue"',
                None]                  # update_field
        ]

        project = Project(owner="lakruzz", number="13")
        # Owner and number are optional - here they are omitted
        result = project.update_field(
            url="https://github.com/lakruzz/gitsquash_lab/issues/7", field="Status", field_value="In Progress")

        # Assertions
        self.assertRegex(result, r"Edited item \".+\"")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_option_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value            
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType',  # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number=13, url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="Blaha")  # Bad field_value

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_type_not_supported(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType',  # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="In Progress")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_descriptor_is_empty(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            # get_field_description empty return value
            [json.dumps({}), Mock(returncode=0, stderr="")]
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError) as e:
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Status", field_value="In Progress")
        self.assertRegex(str(e.exception),
                         r"Field Status not found in project")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_field_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'type': 'UnsupportedFieldType',  # ProjectV2SingleSelectField
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError) as e:
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress")  # bad field name

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_field_id_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'blaha': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',  # id field not found
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress")  # bad field name

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_update_field_field_type_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            ['Status:Pull Request Created', None], # get_project_deliver_field:value
            ["PVT_kwHOAAJfZM4AxVEK", None],  # get_project_id
            ["PVTI_lAHOAAJfZM4AxVEKzgXJ6P4", None],     # add_issue
            [json.dumps({
                'id': 'PVTSSF_lAHOAAJfZM4AxVEKzgndQxI',
                'blaha': 'ProjectV2SingleSelectField',  # id field not found
                'options': [{'name': 'Todo', 'id': 'f75ad846'}, {'name': 'In Progress', 'id': '47fc9ee4'}, {'name': 'Done', 'id': '98236657'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError):
            project.update_field(owner="lakruzz", number="13", url="https://github.com/lakruzz/gitsquash_lab/issues/7",
                                 field="Blaha", field_value="In Progress")  # bad field name

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_invalid_gitroot(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=1, stderr='', stdout='')],  # get_project_root
        ]

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                project = Project()
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Could not determine the git root directory", mock_stderr.getvalue()) 




    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_entire_config_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            # get_project_deliver_field:value
            ['Status:Pull Request Created', None]
        ]

        project = Project()
        self.assertEqual(project.props['project_owner'], "lakruzz")
        self.assertEqual(project.props['project_number'], "13")
        self.assertEqual(project.props['workon_field'], "Status")
        self.assertEqual(project.props['workon_field_value'], "In Progress")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_partial_config_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['', Mock(returncode=1, stderr='Error', stdout='')],  # get_project_workon_field:value
            ['', Mock(returncode=1, stderr='Error', stdout='')]# get_project_deliver_field:value
            
        ]

        project = Project()
        self.assertEqual(project.props['project_owner'], "lakruzz")
        self.assertEqual(project.props['project_number'], "13")
        self.assertEqual(project.props['workon_field'], "Status")
        self.assertEqual(project.props['workon_field_value'], "In Progress")


    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_config_failure(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['', Mock(returncode=1, stderr='Error', stdout='')],  # get_project_owner
            ['', Mock(returncode=1, stderr='Error', stdout='')],  # get_project_number
            ['', Mock(returncode=1, stderr='Error', stdout='')],  # get_project_workon_field:value
            ['', Mock(returncode=1, stderr='Error', stdout='')]# get_project_deliver_field:value
            
        ]

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                project = Project()
       # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Project owner or number not set - null values are currently not supported", mock_stderr.getvalue())  



if __name__ == '__main__':
    unittest.main()
