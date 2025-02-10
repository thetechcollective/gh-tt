import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from project import Project


class TestProject(unittest.TestCase):

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
                'options': [{'name': 'Todo', 'id': 'f75ad846'},{'name': 'In Progress', 'id': '47fc9ee4'},{'name': 'Done', 'id': '98236657'}]
            }), None],                  # get_field_description
            ['Edited item "another new issue"', None]                  # update_field
        ]

        project = Project(owner="lakruzz", number="13")
        result = project.update_field(url="https://github.com/lakruzz/gitsquash_lab/issues/7", field="Status", field_value="In Progress") # Owner and number are optional - here they are omitted

        # Assertions
        self.assertRegex(result, r"Edited item \".+\"")
        mock_gitter_instance.run.assert_called_with(cache=False)

    @patch('project.Gitter')
    def test_update_field_option_not_found(self, MockGitter):
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

    @patch('project.Gitter')
    def test_update_field_type_not_supported(self, MockGitter):
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

    @patch('project.Gitter')
    def test_update_field_descriptor_is_empty(self, MockGitter):
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
            
    @patch('project.Gitter')
    def test_update_field_field_not_found(self, MockGitter):
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

    @patch('project.Gitter')
    def test_update_field_field_id_not_found(self, MockGitter):
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

    @patch('project.Gitter')
    def test_update_field_field_type_not_found(self, MockGitter):
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


    @patch('project.Gitter')
    def test_get_url_from_issue_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/lakruzz/gitsquash_lab/issues/7", Mock(returncode=0, stderr="")]  # get_url_from_issue
        ]

        project = Project(owner="lakruzz", number="13")
        result = project.get_url_from_issue(7)
          
        # Assertions
        self.assertRegex(result, r"https://github.com/lakruzz/.+/7")
        mock_gitter_instance.run.assert_called_with(cache=True)

    @patch('project.Gitter')
    def test_get_url_from_issue_failure(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["https://github.com/lakruzz/gitsquash_lab/issues/7", Mock(returncode=1, stderr="Error message")]  # get_url_from_issue - mimich error
        ]

        project = Project(owner="lakruzz", number="13")
        with self.assertRaises(KeyError) as e:
            result = project.get_url_from_issue(1237)
        self.assertRegex(str(e.exception), r"Could not find issue \d+")            
        
        


if __name__ == '__main__':
    unittest.main()
