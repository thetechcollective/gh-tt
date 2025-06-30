import os
import sys
import unittest

import pytest
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.label import Label


class TestLabel(unittest.TestCase):

    @pytest.mark.dev
    def test_label_no_mock(self):
        label = Label(name='prio 4: wont have')
        
        # Assertions
        self.assertTrue(True)

    @pytest.mark.dev
    def test_label_create_if_not_found(self):
        Gitter().verbose(True)
        label_dev = Label(name='development', create=True)
        label_rework = Label(name='rework', create=True)
        label_adhoc = Label(name='ad hoc', create=True)

        
        # Assertions
        self.assertTrue(True)

    @pytest.mark.unittest
    def test_label_validate_success(self):
        category = "type"
        name = "ad hoc"

        self.assertTrue(Label.validate(name=name, category=category))

    @pytest.mark.unittest
    def test_label_validate_fail(self):
        category = "type"
        name = "some random value that's definitely not a label"

        with pytest.raises(SystemExit):
            Label.validate(name=name, category=category)
