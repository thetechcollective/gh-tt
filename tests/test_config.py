import unittest
import os
import sys
import pytest

class_path = os.path.dirname(os.path.abspath(__file__)) + "/../classes"
sys.path.append(class_path)

from config import Config

class TestProject(unittest.TestCase):

    @pytest.mark.unittest
    def test_read_config_files(self):
        """Test the read_config_files method"""
        config = Config(file='tests/data/.tt-config-good.json')
        self.assertRegex(config.get('config_files')[0], '../.tt-config.json')
        self.assertRegex(config.get('config_files')[2], 'tests/data/.tt-config-good.json')
        self.assertEqual(config.get('project')['owner'], 'thetechcollective')
        self.assertEqual(config.get('wrapup')['policies']['collapse'], True)

    @pytest.mark.unittest
    def test_read_app_defaults(self):
        """Test app defaults"""
        config = Config()
        self.assertEqual(config.get('project')['owner'], '')
        self.assertEqual(config.get('project')['number'], '')

        self.assertEqual(config.get('workon')['status'], 'In Progress')   
        self.assertEqual(config.get('workon')['policies']['rebase'], 'origin/main')   
        self.assertEqual(config.get('workon')['policies']['allow-dirty'], True)   

        self.assertEqual(config.get('wrapup')['status'], 'Delivery Initiated')   
        self.assertEqual(config.get('wrapup')['policies']['collapse'], True)
        self.assertEqual(config.get('wrapup')['policies']['branch'], 'ready/')
        self.assertEqual(config.get('wrapup')['policies']['rebase'], 'origin/main')

        self.assertEqual(config.get('deliver')['policies']['model'], 'branch')
        self.assertEqual(config.get('deliver')['policies']['codeowner'], True)
        