import unittest
import os
import sys
import json
from io import StringIO 
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
import pytest
import asyncio

from gitter import Gitter
from devbranch import Devbranch
from lazyload import Lazyload

class TestLazyLoad(unittest.TestCase):

    @pytest.mark.dev
    def test_manifest_load(self):
        Gitter.verbose = True 
        Gitter.validate_gh_version()
        devbranch = Devbranch()               
        self.assertTrue(True)

   