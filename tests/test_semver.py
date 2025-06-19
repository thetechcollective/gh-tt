import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest

from classes.semver import Semver
from classes.gitter import Gitter

class TestSemver(unittest.TestCase):


    @pytest.mark.dev
    def test_semver_dev(self):
        # Setup
        Gitter.verbose(False)
        semver = Semver()
        semver.list(prerelease=True)
        semver.list(prerelease=False)
        release = semver.get_current_semver()
        prerelease = semver.get_current_semver(prerelease=True)
        semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
        self.assertTrue(semver is not None)

    @pytest.mark.dev
    def test_semver_load_dev(self):
        # Setup
        semver = Semver().from_json('tests/data/semver/semver.json')
        semver.list(prerelease=True)
        semver.list(prerelease=False)
        release = semver.get_current_semver()
        prerelease = semver.get_current_semver(prerelease=True)
        semver.props['semver_tags']['release'] = {}
        
        semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
        self.assertTrue(semver is not None)

