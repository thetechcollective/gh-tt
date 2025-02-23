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
    @patch('project.Gitter')
    def test_update_field_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
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


        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = []

        project = Project(owner="lakruzz", number="13")
        self.assertEqual(project.props['project_owner'], "lakruzz")
        self.assertEqual(project.props['project_number'], "13")

    @pytest.mark.unittest
    @patch('subprocess.run')
    @patch('project.Gitter')
    def test_project_constructor_invalid_gitroot(self, MockGitter, MockSubprocessRun):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['', Mock(returncode=1, stderr='', stdout='')],  # get_project_root

        ]

        # Mock subprocess.run to return an empty result
        MockSubprocessRun.return_value = Mock(
            stdout='', stderr='', returncode=1)

        with self.assertRaises(FileNotFoundError) as e:
            project = Project()
        self.assertRegex(str(e.exception),
                         r"Could not determine the git root directory")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_config_success(self, MockGitter):
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
    def test_project_constructor_read_config_no_owner(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception),
                         r"Project owner not found in the git config")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_project_number(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(e.exception),
                         r"Project number not found in the git config")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_workon_trigger(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['', Mock(return_value=1, stderr='Error')],  # get_project_owner
            # # get_project_deliver_field:value
            ['Status:Pull Request Created', None]

        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(
            e.exception), r"Failed to read workon_field and workon_field_value from the .gitconfig")

    @pytest.mark.unittest
    @patch('project.Gitter')
    def test_project_constructor_read_config_no_deliver_trigger(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ['/workspaces/gh-tt', Mock(returncode=0, stderr='', stdout='')],  # get_project_root
            ['lakruzz', None],  # get_project_owner
            ['13', None],  # get_project_number
            ['Status:In Progress', None],  # get_project_workon_field:value
            # get_project_deliver_field:value
            ['', Mock(return_value=1, stderr='Error')],

        ]

        with self.assertRaises(ValueError) as e:
            project = Project()
        self.assertRegex(str(
            e.exception), r"Failed to read deliver_field and deliver_field_value from the .gitconfig")


if __name__ == '__main__':
    unittest.main()
