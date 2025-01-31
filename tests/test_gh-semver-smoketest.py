import subprocess
import unittest
import pytest
import os
import re
from .testbed import Testbed

class TestGhSemverRunCLI(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        # Class-level setup code
        
        print(f"Setting up testbed for {cls.__name__} class")
        cls.test_dir = os.path.abspath(f"./testbed/{cls.__name__}")
        cls.cli_path = os.path.abspath('gh_semver.py')
        Testbed.create_testbed(cls.test_dir)
        Testbed.git_dataset_1(cls.test_dir)

    @classmethod
    def teardown_class(cls):
        # Class-level teardown code
        print(f"Tearing down {cls.__name__} class testbed")
        print(f"...not doing anything - testbed will be left for inspection and reset as part of the next test run")

    @pytest.mark.smoke
    def test_config_no_switch_no_config(self):
        """Config subcommand used without any of the switches (read config)
        and without any config files"""
        result = Testbed.run_cli(self.cli_path, 'config', cwd=self.test_dir)
        self.assertRegex(result.stdout, r"^$")
        self.assertEqual(result.returncode, 0)

    @pytest.mark.smoke
    def test_no_subcommand_initial(self):
        """Checks if the script returns the default initial version when no config files are setup"""
        result = Testbed.run_cli(self.cli_path, cwd=self.test_dir)
        self.assertRegex(result.stdout, r"^version2.1.1-freetext$")
          
    @pytest.mark.smoke
    def test_config_prefix_switch(self):
        """Config subcommand used to write the prefix to the config files"""
        # Will not require a clean testbed, this is a write operation
        result = Testbed.run_cli(self.cli_path, 'config', '--prefix',  'v', cwd=self.test_dir)
        self.assertEqual(result.returncode, 0)
        result = Testbed.run_cli(self.cli_path, 'config', '--prefix',  'Numb3er', cwd=self.test_dir)
        self.assertGreater(result.returncode, 0)
        self.assertIn(  #try to set it to a non-valid value
            "error: argument --prefix:", result.stderr)
    
    @pytest.mark.smoke
    def test_config_suffix_switch(self):
        """Config subcommand used to write the suffix to the config files"""
        # Will not require a clean testbed, this is a write operation
        result = Testbed.run_cli(self.cli_path, 'config', '--suffix',  'pending', cwd=self.test_dir)
        self.assertEqual(result.returncode, 0)
        result = Testbed.run_cli(self.cli_path, 'config', '--suffix',  'dot.no', cwd=self.test_dir)
        self.assertGreater(result.returncode, 0)
        self.assertIn(  #try to set it to a non-valid value
            "error: argument --suffix:", result.stderr)    
        
    @pytest.mark.smoke
    def test_config_initial_switch(self):
        """Config subcommand used to write the initial to the config files"""
        # Will not require a clean testbed, this is a write operation
        result = Testbed.run_cli(self.cli_path, 'config', '--initial',  '0.0.0', cwd=self.test_dir)
        self.assertEqual(result.returncode, 0)
        result = Testbed.run_cli(self.cli_path, 'config', '--initial',  'v0.0.0', cwd=self.test_dir)
        self.assertGreater(result.returncode, 0)
        self.assertIn(  #try to set it to a non-valid value
            "error: argument --initial:", result.stderr)    

    @pytest.mark.smoke
    def test_no_subcommand_from_config(self):
        """Check if the config files are read correctly"""
        # Even if cwd is not the root of the git repo, the script should still read the .semver.config file
        subprocess.check_call('mkdir not-root', cwd=self.test_dir, shell=True)
        subprocess.check_call('cd not-root', cwd=self.test_dir, shell=True)
        result = Testbed.run_cli(self.cli_path, cwd=self.test_dir+"/not-root")
        self.assertRegex(result.stdout.strip(), r"^version2.1.1-freetext$") 

