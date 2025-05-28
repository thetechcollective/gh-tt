import unittest
import os
import sys
import pytest
from io import StringIO
import sys
from unittest.mock import patch, MagicMock

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from codeowners import Codeowners

class TestCodeowners(unittest.TestCase):

    @pytest.mark.dev
    def test_read_codeowners(self):
        """Test app defaults"""
        codeowners = Codeowners().codeowner_json()
        valid_locations = Codeowners().search_order()
        codeowner_files = Codeowners().file_location(all=True)
        codeowner_file = Codeowners().file_location()

        self.assertTrue(True)

