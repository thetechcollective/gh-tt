import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest
from io import StringIO


from classes.projectitem import Projectitem


class TestProjectItem(unittest.TestCase):


    @pytest.mark.dev
    def test_project_item_history(self):

        data = Projectitem().get_project_item_history(item_id='PVTI_lADOCP77xc4AxZbFzgaEIZY')
        self.assertIsInstance(data, dict)


    @pytest.mark.dev
    def test_project_item_status_change_history(self):

        data = Projectitem().get_status_change_history(item_id='PVTI_lADOCP77xc4AxZbFzgaEIZY')
        self.assertIsInstance(data, dict)


    @pytest.mark.dev
    def test_item_get_created_date(self):

        # Project id: PVT_kwDOCP77xc4AxZbF

        data = Projectitem().get_created_date(item_id='PVTI_lADOCP77xc4AxZbFzgaEIZY')
        self.assertIsInstance(data, str)
        self.assertRegex(data, r'^\d{4}-\d{2}-\d{2}')

