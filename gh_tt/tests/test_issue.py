import pytest

from gh_tt.classes.issue import Issue
from gh_tt.tests.conftest import FakeGitter, FakeProcessResult


@pytest.mark.unittest
def test_issue_constructor_success(monkeypatch, gitter):
    result = """
        {
            "title": "Add a 'deliver' subcommand",
            "url": "https://github.com/thetechcollective/gh-tt/issues/17"
        }
    """

    monkeypatch.setattr("gh_tt.classes.issue.Gitter", gitter(
        stdout=result,
    ))

    issue = Issue.load(number="17")
    
    assert issue.get("number") == 17
    assert issue.get("url") == "https://github.com/thetechcollective/gh-tt/issues/17"
    assert issue.get("title") == "Add a 'deliver' subcommand"