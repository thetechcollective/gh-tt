import subprocess
import unittest
import pytest
import os
from .testbed import Testbed


class TestGhSemverNoSubcommand(unittest.TestCase):

    @classmethod
    def setup_class(cls):
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





