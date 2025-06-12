import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

from classes.semver import Semver

class TestSemver(unittest.TestCase):


    @pytest.mark.unittest
    def test_semver_dev(self):
        # Setup
        semver = Semver()
        self.assertTrue(semver is not None)



