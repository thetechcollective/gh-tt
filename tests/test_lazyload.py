import asyncio
import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from devbranch import Devbranch
from gitter import Gitter
from lazyload import Lazyload


class TestLazyLoad(unittest.TestCase):

    @pytest.mark.dev
    def test_manifest_load(self):
        Gitter.verbose = True 
        Gitter.validate_gh_version()
        devbranch = Devbranch()               
        self.assertTrue(True)

   