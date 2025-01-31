import unittest
import pytest
import os
import subprocess
import sys
from unittest.mock import patch, Mock
from io import StringIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main function from gh-semver.py
from gh_tt import *
from .testbed import Testbed

class TestGhSemverCLIparser(unittest.TestCase):
    """Mostly focused on tesing the CLI, that is the subcommands, arguments and options"""

    @classmethod
    def setup_class(cls):
        print(f"Setting up testbed for {cls.__name__} class")
#        cls.test_dir = os.path.abspath(f"./testbed/{cls.__name__}")
#        cls.cli_path = os.path.abspath('gh-semver.py')
#        Testbed.create_testbed(cls.test_dir)
#        Testbed.git_dataset_1(cls.test_dir)

    @classmethod
    def teardown_class(cls):
        # Class-level teardown code
        print(f"Tearing down {cls.__name__} class testbed")
        
    @pytest.mark.dev
    def test_bump_invalid_argument(self):
        args = ['bump', '--major', '--no-run', "--invalid"]
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                parse(args)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("unrecognized arguments: --invalid", mock_stderr.getvalue())

    @pytest.mark.dev
    def test_bump_full_monty(self):
        args = ['bump', '--minor', '--message', 'Additional message', '--suffix', 'pending']
        valid = parse(args)
        self.assertEqual(valid.command, 'bump')
        self.assertTrue(valid.minor)
        self.assertTrue(valid.run)    

    @pytest.mark.dev
    def test_bump_invalid_suffix(self):
        args = ['bump', '--minor', '--suffix', 'Pending']
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                parse(args)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("Suffix: Allowed characters are lowercase letters, numbers, dashes and underscores", mock_stderr.getvalue())

    @pytest.mark.dev
    def test_config(self):
        args = ['config', '--prefix', 'ver', '--suffix', 'dev', '--initial', '1.0.0']
        valid = parse(args)
        self.assertEqual(valid.command, 'config')
        self.assertEqual(valid.prefix, 'ver')
        self.assertEqual(valid.suffix, 'dev')
        self.assertEqual(valid.initial, '1.0.0')


    @pytest.mark.dev
    def test_config_invalid_initial(self):
        args = ['config', '--prefix', 'ver', '--suffix', 'dev', '--initial', '1.NO.0']
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                parse(args)
            self.assertEqual(cm.exception.code, 2)
            stderr = mock_stderr.getvalue()
            self.assertIn("Initial offset: Must be a three-level integer separated by dots (e.g. 1.0.0)", stderr)

    @pytest.mark.dev
    def test_config_invalid_prefix(self):
        args = ['config', '--prefix', 'Numb3r', '--suffix', 'dev', '--initial', '1.0.0']
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                parse(args)
            self.assertEqual(cm.exception.code, 2)
            stderr = mock_stderr.getvalue()
            self.assertIn("Prefix: Allowed characters are lowercase and uppercase letters", stderr)

    @pytest.mark.dev
    def test_bump(self):
        args = ['bump', '--major', '--no-run']
        valid = parse(args)
        self.assertEqual(valid.command, 'bump')
        self.assertTrue(valid.major)
        self.assertFalse(valid.run)

class TestGhSemverUnitTest_testdata(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        print(f"Setting up {cls.__name__} class")
        cls.test_dir = os.path.abspath(f"./testbed/{cls.__name__}")
        cls.cli_path = os.path.abspath('gh-semver.py')
        Testbed.create_testbed(cls.test_dir)
        Testbed.git_dataset_1(cls.test_dir)


    @classmethod
    def teardown_class(cls):
        # Class-level teardown code
        print(f"Tearing down {cls.__name__} class")

    @pytest.mark.dev
    def test_get_tag_major(self): 
        semver = Semver(workdir=self.test_dir)

        cmd = semver.get_git_tag_cmd(level='major', message='Additional message', suffix='pending')
        self.assertRegex(cmd, r'^git tag -a -m')
        self.assertRegex(cmd, r'Additional message"')
        self.assertRegex(cmd, r"3.0.0-pending$")

        new_tag = semver.bump(level='major', message='Additional message', suffix='pending')
        self.assertRegex(new_tag, r"3.0.0-pending$") 
        
        cmd = semver.bump(level='minor')
        self.assertRegex(cmd, r"3.1.0$")

        cmd = semver.bump(level='patch')
        self.assertRegex(cmd, r"3.1.1$")

   


class TestGhSemverUnitTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        print(f"Setting up {cls.__name__} class")
        cls.test_dir = os.path.abspath(f"./testbed/{cls.__name__}")
        cls.cli_path = os.path.abspath('gh-semver.py')
        Testbed.create_testbed(cls.test_dir)


    @classmethod
    def teardown_class(cls):
        # Class-level teardown code
        print(f"Tearing down {cls.__name__} class")

    @pytest.mark.dev
    def test_config(self):
        subprocess.run('rm .semver.config', cwd=self.test_dir, shell=True)       
        semver = Semver(workdir=self.test_dir)
        self.assertRegex(semver.prefix, r"^$")
        self.assertRegex(semver.initial, r"^0.0.0$")
        self.assertRegex(semver.suffix, r"^$")

        semver.set_config(prefix='ver', initial='1.0.0', suffix='pending')
        self.assertRegex(semver.prefix, r"^ver$")
        self.assertRegex(semver.initial, r"^1.0.0$")
        self.assertRegex(semver.suffix, r"^pending$")

        cmd = semver.get_git_tag_cmd(level='minor')
        self.assertRegex(cmd, r"ver1.1.0-pending$")

    @pytest.mark.dev
    def test_semver_null_constructor(self):
        semver = Semver()
        cwd = os.getcwd()
        self.assertEqual(semver.workdir, cwd)

    @pytest.mark.dev
    def test_bad_config(self):
        subprocess.check_call('echo "[semver]\\n  prefix = ver\\n  initial = 1.hey.0\\n  suffix = pending">.semver.config', cwd=self.test_dir, shell=True)       
        stderr = None
        try:
            semver = Semver(workdir=self.test_dir)
        except ValueError as e:
            stderr = str(e)
        self.assertRegex(stderr, r"Failed to parse initial version, doesn't look like a three-level integer") 
        
    @pytest.mark.dev
    def test_semver_bad_workdir(self):
        stderr = None
        try:
            semver = Semver(workdir='bad_dir_xyz')
        except FileNotFoundError as e:
            stderr = str(e)    
        self.assertEqual(stderr, 'Directory bad_dir_xyz does not exist')

    @pytest.mark.dev
    @patch.object(Semver, '_Semver__run_git')
    def test_semver_outside_git(self, mock_run_git):
        # Simulate the git command returning an error
        mock_run_git.return_value = Mock(
            returncode=1, 
            stderr='fatal: not a git repository (or any of the parent directories): .git\n')

        with self.assertRaises(FileNotFoundError) as context:
            semver = Semver()

        self.assertIn('fatal: not a git repository (or any of the parent directories): .git\n', str(context.exception))



if __name__ == '__main__':
    unittest.main()