import json
import tempfile
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from gh_tt.classes.config import Config
from gh_tt.classes.label import Label


@pytest.mark.unittest
def test_label_validate_success():
    category = "type"
    name = "ad hoc"

    assert Label.validate(name=name, category=category)

@pytest.mark.unittest
def test_label_validate_fail():
    category = "type"
    name = "some random value that's definitely not a label"

    with pytest.raises(SystemExit):
        Label.validate(name=name, category=category)

@pytest.mark.unittest
def test_label_create_true_calls_create_new(mocker: MockerFixture):
    create_new = mocker.patch('gh_tt.classes.label.Label._create_new')
    mocker.patch('gh_tt.classes.label.Label._reload')

    label_name = 'new-label'

    label_string = json.dumps({
        'labels': {

        label_name: {
          "color": "00aa00",
          "description": "Test label",
          "category": "type"
        },
        }
    })
    config_file = tempfile.mkstemp(text=True)[1]
    Path(config_file).write_text(label_string)

    Config.add_config(config_file=config_file)
    Label(name='new-label', create=True)

    create_new.assert_called_once()
