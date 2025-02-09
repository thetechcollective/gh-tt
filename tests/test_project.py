import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from project import Project


class TestProject(unittest.TestCase):

    @patch('project.Gitter')
    def test_update_field_success(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["project_id_123", None],  # get_project_id
            ["item_id_456", None],     # add_issue
            [json.dumps({
                'id': 'field_id_789',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'field_value', 'id': 'option_id_101'}]
            }), None],                 # get_field_description
            ["", None]                 # update_field
        ]

        project = Project(owner="owner", number="number")
        result = project.update_field(
            owner="owner", number=1, url="http://example.com", field="field_name", field_value="field_value")

        # Assertions
        self.assertEqual(result, "")
        mock_gitter_instance.run.assert_called_with(cache=False)

    @patch('project.Gitter')
    def test_update_field_field_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["project_id_123", None],  # get_project_id
            ["item_id_456", None],     # add_issue
            [json.dumps({
                'id': 'field_id_789',
                'type': 'ProjectV2SingleSelectField',
                'options': []
            }), None]                  # get_field_description
        ]

        project = Project(owner="owner", number="number")
        with self.assertRaises(RuntimeError):
            project.update_field(owner="owner", number=1, url="http://example.com",
                                 field="field_name", field_value="field_value")

    @patch('project.Gitter')
    def test_update_field_option_not_found(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["project_id_123", None],  # get_project_id
            ["item_id_456", None],     # add_issue
            [json.dumps({
                'id': 'field_id_789',
                'type': 'ProjectV2SingleSelectField',
                'options': [{'name': 'other_value', 'id': 'option_id_101'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="owner", number="number")
        with self.assertRaises(RuntimeError):
            project.update_field(owner="owner", number=1, url="http://example.com",
                                 field="field_name", field_value="field_value")

    @patch('project.Gitter')
    def test_update_field_type_not_supported(self, MockGitter):
        # Setup
        mock_gitter_instance = MockGitter.return_value
        mock_gitter_instance.run.side_effect = [
            ["project_id_123", None],  # get_project_id
            ["item_id_456", None],     # add_issue
            [json.dumps({
                'id': 'field_id_789',
                'type': 'UnsupportedFieldType',
                'options': [{'name': 'field_value', 'id': 'option_id_101'}]
            }), None]                  # get_field_description
        ]

        project = Project(owner="owner", number="number")
        with self.assertRaises(RuntimeError):
            project.update_field(owner="owner", number=1, url="http://example.com",
                                 field="field_name", field_value="field_value")


if __name__ == '__main__':
    unittest.main()
