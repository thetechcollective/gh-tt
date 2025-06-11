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

from label import Label
from issue import Issue
from devbranch import Devbranch
from gitter import Gitter

class TestLabel(unittest.TestCase):

    @pytest.mark.dev
    def test_label_no_mock(self):
        label = Label(name='prio 4: wont have')
        
        # Assertions
        self.assertTrue(True)

    @pytest.mark.dev
    def test_label_create_if_not_found(self):
        Gitter().verbose(True)
        label_dev = Label(name='development', create=True)
        label_rework = Label(name='rework', create=True)
        label_adhoc = Label(name='ad hoc', create=True)

        
        # Assertions
        self.assertTrue(True)
