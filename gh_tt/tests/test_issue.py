import pytest

from gh_tt.classes.issue import Issue


@pytest.mark.unittest
def test_issue_constructor_success(mocker):
    result = """
        {
            "title": "Add a 'deliver' subcommand",
            "url": "https://github.com/thetechcollective/gh-tt/issues/17"
        }
    """

    mocker.patch(
        'gh_tt.classes.gitter.Gitter.run',
        return_value=(result, mocker.Mock())
    )

    issue = Issue.load(number="17")
    
    assert issue.get("number") == str(17)
    assert issue.get("url") == "https://github.com/thetechcollective/gh-tt/issues/17"
    assert issue.get("title") == "Add a 'deliver' subcommand"
