import unittest
import os
import sys
import pytest
from io import StringIO
import sys
from unittest.mock import patch, MagicMock

from responsibles import Responsibles
from gitter import Gitter

class TestResponsibles(unittest.TestCase):

    @pytest.mark.dev
    def test_read_responsibles(self):
        """Test app defaults"""
        codeowners = Responsibles().responsibles_json()
        valid_locations = Responsibles().search_order()
        codeowner_files = Responsibles().file_location(all=True)
        codeowner_file = Responsibles().file_location()

        self.assertTrue(True)

    @pytest.mark.dev
    def test_parse_responsibles(self):
        """Test app defaults"""
        codeowners = Responsibles().codeowners_parse(
            changeset=["README.md", 
                       "src/main.py", 
                       "docs/index.md", 
                       "hmm/src/data/data.json", 
                       "hmm/src/db/data/other.json",
                       "hmm/src/db/README.md",
                       "hmm/db/README.md"],
            exclude=["@albertbanke"]
        )    
        responsibels = Responsibles().responsibles_parse(
            changeset=["README.md", 
                       "src/main.py", 
                       "docs/index.md", 
                       "hmm/src/data/data.json", 
                       "hmm/src/db/data/other.json",
                       "hmm/src/db/README.md",
                       "hmm/db/README.md"],
            exclude=["@albertbanke"]
        )

        markdown = Responsibles().responsibles_as_markdown(
            changeset=["README.md", 
                       "src/main.py", 
                       "docs/index.md", 
                       "hmm/src/data/data.json", 
                       "hmm/src/db/data/other.json",
                       "hmm/src/db/README.md",
                       "hmm/db/README.md"],
            exclude=["@albertbanke"]
        )

        self.assertTrue(True)


    @pytest.mark.dev
    def test_is_responsible(self):
        """Test app defaults"""
        Gitter().verbose = True
        all = Responsibles().is_member('@thetechcollective/all', '@lakruzz')
        ai_gov = Responsibles().is_member('@thetechcollective/ai-gov', '@lakruzz')
        arla_devx = Responsibles().is_member('@arla-omb/devx', '@lakruzz')


        self.assertTrue(True)