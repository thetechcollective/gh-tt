import json

import pytest

from gh_tt.classes.status import _check_pending_workflows, _get_icon, _process_statuses


@pytest.mark.unittest
def test_check_pending_workflows_with_pending(mocker):
    """Test that pending workflows are detected correctly"""

    mock_workflows = [
        {
            "status": "in_progress",
            "conclusion": None,
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "test-workflow",
            "workflowName": "Test Workflow"
        },
        {
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "other-workflow", 
            "workflowName": "Other Workflow"
        }
    ]

    mock_gitter = mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(json.dumps(mock_workflows), mocker.Mock())
    )
    
    result = _check_pending_workflows("abc123")
    
    assert result
    mock_gitter.assert_called_once()


@pytest.mark.unittest
def test_check_pending_workflows_all_complete(mocker):
    """Test that completed workflows return False"""
    
    mock_workflows = [
        {
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "test-workflow",
            "workflowName": "Test Workflow"
        },
        {
            "status": "completed",
            "conclusion": "failure",
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "other-workflow",
            "workflowName": "Other Workflow"
        }
    ]

    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(json.dumps(mock_workflows), mocker.Mock())
    )
    
    result = _check_pending_workflows("abc123")
    
    assert not result

@pytest.mark.unittest
def test_check_pending_workflows_queued_status(mocker):
    """Test that queued workflows are detected as pending"""
    
    mock_workflows = [
        {
            "status": "queued",
            "conclusion": None,
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "queued-workflow",
            "workflowName": "Queued Workflow"
        }
    ]

    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(json.dumps(mock_workflows), mocker.Mock())
    )
    
    result = _check_pending_workflows("abc123")
    assert result

@pytest.mark.unittest
def test_check_pending_workflows_waiting_status(mocker):
    """Test that waiting workflows are detected as pending"""
    mock_workflows = [
        {
            "status": "waiting",
            "conclusion": None,
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "waiting-workflow",
            "workflowName": "Waiting Workflow"
        }
    ]
    
    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(json.dumps(mock_workflows), mocker.Mock())
    )

    result = _check_pending_workflows("abc123")
    assert result is True

@pytest.mark.unittest
def test_check_pending_workflows_no_workflows(mocker):
    """Test that empty workflow list returns False"""
    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=('', mocker.Mock())
    )

    result = _check_pending_workflows("abc123")
    assert not result

@pytest.mark.unittest
def test_check_pending_workflows_empty_json(mocker):
    """Test that empty JSON array returns False"""
    
    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=('[]', mocker.Mock())
    )

    result = _check_pending_workflows("abc123")
    assert not result

@pytest.mark.unittest
def test_check_pending_workflows_exception_handling(mocker):
    """Test that exceptions are handled gracefully"""

    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(Exception("API Error"), mocker.Mock())
    )
    
    result = _check_pending_workflows("abc123")
    assert not result

@pytest.mark.unittest
def test_check_pending_workflows_invalid_json(mocker):
    """Test that invalid JSON is handled gracefully"""
    
    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=("invalid json", mocker.Mock())
    )

    result = _check_pending_workflows("abc123")
    assert not result

@pytest.mark.unittest
def test_check_pending_workflows_missing_status_field(mocker):
    """Test workflows with missing status field"""
    mock_workflows = [
        {
            "conclusion": "success",
            "createdAt": "2023-01-01T00:00:00Z",
            "name": "test-workflow",
            "workflowName": "Test Workflow"
            # Missing 'status' field
        }
    ]
    
    mocker.patch(
        'gh_tt.classes.status.Gitter.run',
        return_value=(json.dumps(mock_workflows), mocker.Mock())
    )

    result = _check_pending_workflows("abc123")
    assert result is False


@pytest.mark.unittest
def test_get_icon_success():
    """Test success icon"""
    assert _get_icon('success') == "✅"

@pytest.mark.unittest
def test_get_icon_failure():
    """Test failure icon"""
    assert _get_icon('failure') == "❌"

@pytest.mark.unittest
def test_get_icon_error():
    """Test error icon"""
    assert _get_icon('error') == "💥"

@pytest.mark.unittest
def test_get_icon_pending():
    """Test pending icon"""
    assert _get_icon('pending') == "⏳"

@pytest.mark.unittest
def test_get_icon_unknown():
    """Test unknown state returns question mark"""
    assert _get_icon('unknown_state') == "❓"

@pytest.mark.unittest
def test_get_icon_empty_string():
    """Test empty string returns question mark"""
    assert _get_icon('') == "❓"


@pytest.mark.unittest
def test_process_statuses_all_success():
    """Test processing all successful statuses"""
    statuses = [
        {'context': 'ci/test', 'state': 'success'},
        {'context': 'ci/build', 'state': 'success'}
    ]

    all_complete, all_success, lines_printed = _process_statuses(statuses)
    
    assert all_complete
    assert all_success
    assert lines_printed == 2

@pytest.mark.unittest
def test_process_statuses_with_pending():
    """Test processing statuses with pending ones"""
    statuses = [
        {'context': 'ci/test', 'state': 'success'},
        {'context': 'ci/build', 'state': 'pending'}
    ]
    
    all_complete, all_success, lines_printed = _process_statuses(statuses)
    
    assert not all_complete
    assert all_success  # pending doesn't affect success flag
    assert lines_printed == 2

@pytest.mark.unittest
def test_process_statuses_with_failure():
    """Test processing statuses with failures"""
    statuses = [
        {'context': 'ci/test', 'state': 'success'},
        {'context': 'ci/build', 'state': 'failure'}
    ]
    
    all_complete, all_success, lines_printed = _process_statuses(statuses)
    
    assert all_complete
    assert not all_success
    assert lines_printed == 2

@pytest.mark.unittest
def test_process_statuses_prints_sorted(capsys):
    """Test processing statuses with failures"""
    statuses = [
        {'context': 'ci/b_test', 'state': 'failure'},
        {'context': 'ci/0_test', 'state': 'success'},
        {'context': 'ci/a_test', 'state': 'success'},
        {'context': 'ci/1_test', 'state': 'success'},
    ]
    
    _process_statuses(statuses)
    
    output = capsys.readouterr().out
    lines = output.strip().split('\n')

    assert 'ci/0_test' in lines[0]
    assert 'ci/1_test' in lines[1]
    assert 'ci/a_test' in lines[2]
    assert 'ci/b_test' in lines[3]

@pytest.mark.unittest
def test_process_statuses_empty_list():
    """Test processing empty status list"""
    statuses = []
    
    all_complete, all_success, lines_printed = _process_statuses(statuses)
    
    assert all_complete is True
    assert all_success is True
    assert lines_printed == 0

@pytest.mark.unittest
def test_process_statuses_missing_fields(capsys):
    """Test processing statuses with missing fields"""
    statuses = [
        {'context': 'ci/test'},  # Missing state
        {'state': 'success'}     # Missing context
    ]
    
    _, _, lines_printed = _process_statuses(statuses)
    
    output = capsys.readouterr().out
    assert lines_printed == 2
    assert "❓ ci/test: [unknown]" in output
    assert "✅ unknown: [success]" in output
