import pytest

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
