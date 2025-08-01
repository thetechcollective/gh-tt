from dataclasses import dataclass

import pytest

from gh_tt.classes.issue import Issue


@dataclass
class FakeProcessResult:
    returncode: int
    stderr: str = ""
    stdout: str = ""

@dataclass
class FakeGitter:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""

    def run(self):
        return (self.stdout, FakeProcessResult(returncode=self.returncode, stderr=self.stderr, stdout=self.stdout))


@pytest.mark.unittest
def test_issue_constructor_success(monkeypatch):
    result = """
        {
            "title": "Add a 'deliver' subcommand",
            "url": "https://github.com/thetechcollective/gh-tt/issues/17"
        }
    """

    monkeypatch.setattr("gh_tt.classes.issue.Gitter", FakeGitter(
        stdout=result,
    ))

    issue = Issue.load(number="17")

    assert issue.get("number") == 17
    assert issue.get("url") == "https://github.com/thetechcollective/gh-tt/issues/17"
    assert issue.get("title") == "Add a 'deliver' subcommand"