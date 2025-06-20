import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest


from semver import Semver
from gitter import Gitter

class TestSemver(unittest.TestCase):


    @pytest.mark.unittest
    def test_semver_dev(self):
        # Setup
        Gitter.verbose = False
        semver = Semver()
        self.assertIsInstance(semver, Semver)
        self.assertEqual(semver.get('initial'), '0.0.0')
        semver = None

        semver = Semver(suffix='pending', prefix='v', initial='1.4.1')
        self.assertIsInstance(semver, Semver)
        self.assertEqual(semver.get('initial'), '1.4.1')
        self.assertEqual(semver.get('suffix'), 'pending')
        self.assertEqual(semver.get('prefix'), 'v')

        semver = None

        with patch('sys.stdout', new=StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                semver = Semver(initial='bad.initial.3')
            output = fake_out.getvalue()
            # Adjust the expected error message as per your Semver implementation
            self.assertIn("Invalid initial version", output)

        semver = Semver().from_json('tests/data/semver/semver_loaded_release.json')
        semver = Semver()
        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            semver.list(prerelease=True)
            output = fake_out.getvalue()
            # Check that output contains a list of labels (assuming labels are printed as strings)
            self.assertIn("1.0.1-rc\n", output)
            self.assertIn("1.0.11rc\n", output)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            semver.list(prerelease=False)
            output = fake_out.getvalue()
            # Check that output contains a list of labels (assuming labels are printed as strings)
            self.assertIn("0.7.3\n", output)
            self.assertIn("0.6.1\n", output)

        release = semver.get_current_semver()
        self.assertEqual(release, '0.7.3')

        prerelease = semver.get_current_semver(prerelease=True)
        self.assertEqual(prerelease, '1.0.11rc')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
            output = fake_out.getvalue()
            # Check that output contains a list of labels (assuming labels are printed as strings)
            self.assertIn('git tag -a -m "1.0.12rc\nBumped patch from version \'1.0.11rc\' to \'1.0.12rc\'\nTest patch bump" 1.0.12rc\n', output)


    @pytest.mark.unittest
    def test_semver_load_dev(self):
        # Setup
        semver = Semver().from_json('tests/data/semver/semver_loaded_release.json')
        semver.list(prerelease=True)
        semver.list(prerelease=False)
        release = semver.get_current_semver()
        prerelease = semver.get_current_semver(prerelease=True)
        semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
        self.assertTrue(semver is not None)

