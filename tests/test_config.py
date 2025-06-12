import unittest
import os
import sys
import pytest
from io import StringIO
import sys
from unittest.mock import patch, MagicMock

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from config import Config

class TestProject(unittest.TestCase):

    @pytest.mark.unittest
    def test_read_app_defaults_static(self):
        """Test app defaults"""
        config = Config.config()
        files = Config.config_files()
        self.assertEqual(len(files), 2)
        self.assertRegex(files[0], '../.tt-config.json')    
        self.assertEqual(config['project']['owner'], '')
        self.assertEqual(config['project']['number'], '')
        self.assertEqual(config['workon']['status'], 'In Progress')   
        self.assertEqual(config['workon']['labels']['title'], 'ad hoc')
        self.assertEqual(config['workon']['labels']['issue'], 'development')
        self.assertEqual(config['workon']['labels']['rework'], 'rework')
        self.assertEqual(config['squeeze']['policies']['abort_for_rebase'], True)   
        self.assertEqual(config['squeeze']['policies']['allow-dirty'], True)   
        self.assertEqual(config['squeeze']['policies']['allow-staged'], False)
        self.assertEqual(config['squeeze']['policies']['quiet'], False)
        self.assertEqual(config['squeeze']['policies']['close-keyword'], 'resolves')
        self.assertEqual(config['wrapup']['policies']['warn_about_rebase'], True)
        self.assertEqual(config['deliver']['status'], 'Delivery Initiated')   
        self.assertEqual(config['deliver']['policies']['branch_prefix'], 'ready')
        self.assertRegex(config['labels']['ad hoc']['color'], r'[0-9a-fA-F]{6}')
        self.assertRegex(config['labels']['ad hoc']['description'], r'.*')
        self.assertLessEqual(len(config['labels']['ad hoc']['description']), 100)  
        self.assertRegex(config['labels']['rework']['color'], r'[0-9a-fA-F]{6}')
        self.assertRegex(config['labels']['rework']['description'], r'.*')
        self.assertLessEqual(len(config['labels']['rework']['description']), 100)   
        self.assertRegex(config['labels']['development']['color'], r'[0-9a-fA-F]{6}')
        self.assertRegex(config['labels']['development']['description'], r'.*')
        self.assertLessEqual(len(config['labels']['development']['description']), 100) 

    @pytest.mark.unittest
    def test_read_project_static(self):
        """Test project specifics """
        config = Config.add_config('tests/data/.tt-config-project.json')
        files = Config.config_files()
        self.assertEqual(len(files), 3)
        self.assertRegex(files[2], '.tt-config-project.json')    
        self.assertEqual(config['project']['owner'], 'thetechcollective')
        self.assertEqual(config['project']['number'], '12')
        self.assertEqual(config['wrapup']['policies']['warn_about_rebase'], False)   
        self.assertEqual(config['wrapup']['policies']['allow-dirty'], False) 
        self.assertEqual(config['squeeze']['policies']['close-keyword'], 'resolves')

    @pytest.mark.unittest
    def test_read_malformed_static_exit(self):
        """Test malformed config exits with error"""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                Config.add_config('tests/data/.tt-config-malformed.json')

        # Assertions
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Could not parse JSON", mock_stderr.getvalue())

    @pytest.mark.unittest
    def test_read_nonexisting_static_exit(self):
        """Test nonexisting config exits with error"""
        with self.assertRaises(FileNotFoundError) as cm:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                Config.add_config('tests/data/.tt-config-nonexisting.json')
        # Assertions
        self.assertIn("No such file or directory", str(cm.exception))

