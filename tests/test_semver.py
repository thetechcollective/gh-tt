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
    @patch('sys.stderr', new_callable=StringIO)
    def test_semver_init(self, mock_stderr):
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

        with self.assertRaises(SystemExit) as cm:
            semver = Semver(initial='bad.initial.3')

        self.assertEqual(cm.exception.code, 1)
        self.assertRegex(mock_stderr.getvalue(), r"Invalid initial version" )
        

    @pytest.mark.unittest
    @patch('sys.stdout', new_callable=StringIO)
    def test_semver_list(self, mock_stdout):
        # Setup
        semver = Semver().from_json('tests/data/semver/semver_loaded_release_and_prerelease.json')
        self.assertIsInstance(semver, Semver)

        mock_stdout.flush()
        semver.list(prerelease=True)
        self.assertIn("1.0.1-rc\n", mock_stdout.getvalue())
        self.assertIn("1.0.11rc\n", mock_stdout.getvalue())
        mock_stdout.flush()

        mock_stdout.flush()
        semver.list(prerelease=False)
        self.assertIn("0.7.3\n", mock_stdout.getvalue())
        self.assertIn("0.6.1\n", mock_stdout.getvalue())
        mock_stdout.flush()

        release = semver.get_current_semver()
        self.assertEqual(release, '0.7.3')

        prerelease = semver.get_current_semver(prerelease=True)
        self.assertEqual(prerelease, '1.0.11rc')

        mock_stdout.flush()
        semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
        self.assertIn('git tag -a -m "1.0.12rc\nBumped patch from version \'1.0.11rc\' to \'1.0.12rc\'\nTest patch bump" 1.0.12rc\n', mock_stdout.getvalue())

    @pytest.mark.unittest
    @patch('sys.stdout', new_callable=StringIO)
    def test_semver_first_prerelease(self, mock_stdout):
        # Setup
        semver = Semver().from_json('tests/data/semver/semver_loaded_release.json')
        self.assertIsInstance(semver, Semver)

        semver.list(prerelease=True)
        self.assertEqual('', mock_stdout.getvalue())
        # Reset mock_stdout properly
        mock_stdout.seek(0)
        mock_stdout.truncate(0)
        
        # Test release list
        semver.list(prerelease=False)
        self.assertIn("0.7.3\n", mock_stdout.getvalue())
        self.assertIn("0.6.1\n", mock_stdout.getvalue())
        # Reset mock_stdout properly
        mock_stdout.seek(0)
        mock_stdout.truncate(0)
        
        # Test current versions
        release = semver.get_current_semver()
        self.assertEqual(release, '0.7.3')

        prerelease = semver.get_current_semver(prerelease=True)
        self.assertEqual(prerelease, None)

        semver.bump('patch', message='Test patch bump', prerelease=True, dry_run=True)
        self.assertIn('git tag -a -m "0.0.1rc\nBumped patch from version \'None\' to \'0.0.1rc\'\nTest patch bump" 0.0.1rc\n', mock_stdout.getvalue())



    @pytest.mark.dev
    def test_semver_dev(self):
        # Setup
        semver = Semver()
        pre_note = semver.note(prerelease=True)
        print (pre_note)
        self.assertIsInstance(pre_note, str)

        note = semver.note()
        print (note)
  
        note = semver.note(filename='temp/release_notes.md')
