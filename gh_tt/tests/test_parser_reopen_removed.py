import pytest
from unittest.mock import Mock, patch

from gh_tt.modules.tt_parser import tt_parse


@pytest.mark.unittest
def test_workon_reopen_flag_removed():
    """Test that --reopen flag has been removed from the workon parser"""
    
    # Attempt to parse with --reopen flag should fail with SystemExit
    with pytest.raises(SystemExit) as exc_info:
        tt_parse(['workon', '-i', '123', '--reopen'])
    
    # Verify it exits with error code 2 (argparse unrecognized arguments error)
    assert exc_info.value.code == 2


@pytest.mark.unittest
def test_workon_closed_issue_fails(mocker):
    """Test that working on a closed issue always fails"""
    
    # Mock a closed issue
    mock_issue = Mock()
    mock_issue.get = Mock(side_effect=lambda key: {
        'title': 'Closed Issue',
        'url': 'https://github.com/test/repo/issues/123',
        'closed': True
    }.get(key))
    
    mocker.patch(
        'gh_tt.classes.issue.Issue.load',
        return_value=mock_issue
    )
    
    # Mock Devbranch._assert_props to avoid actual git operations
    mocker.patch(
        'gh_tt.classes.devbranch.asyncio.run',
        return_value=None
    )
    
    # Mock the devbranch properties
    from gh_tt.classes.devbranch import Devbranch
    devbranch = Devbranch()
    devbranch.set('remote', 'origin')
    devbranch.set('default_branch', 'main')
    
    # Should exit with error when trying to work on closed issue
    with pytest.raises(SystemExit) as exc_info:
        devbranch.set_issue(issue_number=123)
    
    # Verify exit code
    assert exc_info.value.code == 1

