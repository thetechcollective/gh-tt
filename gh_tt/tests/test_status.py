import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gh_tt.classes.status import _check_pending_workflows, _get_icon, _process_statuses, Status


class TestCheckPendingWorkflows:
    """Test cases for the _check_pending_workflows function"""
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_with_pending(self, mock_gitter, mock_asyncio_run):
        """Test that pending workflows are detected correctly"""
        # Setup mock data with pending workflow
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
        
        mock_result = json.dumps(mock_workflows)
        mock_asyncio_run.return_value = [mock_result, None]
        
        # Test
        result = _check_pending_workflows("abc123")
        
        # Assertions
        assert result is True
        mock_gitter.assert_called_once()
        mock_asyncio_run.assert_called_once()
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_all_complete(self, mock_gitter, mock_asyncio_run):
        """Test that completed workflows return False"""
        # Setup mock data with only completed workflows
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
        
        mock_result = json.dumps(mock_workflows)
        mock_asyncio_run.return_value = [mock_result, None]
        
        # Test
        result = _check_pending_workflows("abc123")
        
        # Assertions
        assert result is False
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_queued_status(self, mock_gitter, mock_asyncio_run):
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
        
        mock_result = json.dumps(mock_workflows)
        mock_asyncio_run.return_value = [mock_result, None]
        
        result = _check_pending_workflows("abc123")
        assert result is True
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_waiting_status(self, mock_gitter, mock_asyncio_run):
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
        
        mock_result = json.dumps(mock_workflows)
        mock_asyncio_run.return_value = [mock_result, None]
        
        result = _check_pending_workflows("abc123")
        assert result is True
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_no_workflows(self, mock_gitter, mock_asyncio_run):
        """Test that empty workflow list returns False"""
        mock_asyncio_run.return_value = ["", None]
        
        result = _check_pending_workflows("abc123")
        assert result is False
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_empty_json(self, mock_gitter, mock_asyncio_run):
        """Test that empty JSON array returns False"""
        mock_asyncio_run.return_value = ["[]", None]
        
        result = _check_pending_workflows("abc123")
        assert result is False
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_exception_handling(self, mock_gitter, mock_asyncio_run):
        """Test that exceptions are handled gracefully"""
        mock_asyncio_run.side_effect = Exception("API Error")
        
        result = _check_pending_workflows("abc123")
        assert result is False
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_invalid_json(self, mock_gitter, mock_asyncio_run):
        """Test that invalid JSON is handled gracefully"""
        mock_asyncio_run.return_value = ["invalid json", None]
        
        result = _check_pending_workflows("abc123")
        assert result is False
    
    @pytest.mark.unittest
    @patch('gh_tt.classes.status.asyncio.run')
    @patch('gh_tt.classes.status.Gitter')
    def test_check_pending_workflows_missing_status_field(self, mock_gitter, mock_asyncio_run):
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
        
        mock_result = json.dumps(mock_workflows)
        mock_asyncio_run.return_value = [mock_result, None]
        
        result = _check_pending_workflows("abc123")
        assert result is False


class TestGetIcon:
    """Test cases for the _get_icon function"""
    
    @pytest.mark.unittest
    def test_get_icon_success(self):
        """Test success icon"""
        assert _get_icon('success') == "✅"
    
    @pytest.mark.unittest
    def test_get_icon_failure(self):
        """Test failure icon"""
        assert _get_icon('failure') == "❌"
    
    @pytest.mark.unittest
    def test_get_icon_error(self):
        """Test error icon"""
        assert _get_icon('error') == "💥"
    
    @pytest.mark.unittest
    def test_get_icon_pending(self):
        """Test pending icon"""
        assert _get_icon('pending') == "⏳"
    
    @pytest.mark.unittest
    def test_get_icon_unknown(self):
        """Test unknown state returns question mark"""
        assert _get_icon('unknown_state') == "❓"
    
    @pytest.mark.unittest
    def test_get_icon_empty_string(self):
        """Test empty string returns question mark"""
        assert _get_icon('') == "❓"


class TestProcessStatuses:
    """Test cases for the _process_statuses function"""
    
    @pytest.mark.unittest
    @patch('builtins.print')
    def test_process_statuses_all_success(self, mock_print):
        """Test processing all successful statuses"""
        statuses = [
            {'context': 'ci/test', 'state': 'success'},
            {'context': 'ci/build', 'state': 'success'}
        ]
        
        all_complete, all_success, lines_printed = _process_statuses(statuses)
        
        assert all_complete is True
        assert all_success is True
        assert lines_printed == 2
        assert mock_print.call_count == 2
    
    @pytest.mark.unittest
    @patch('builtins.print')
    def test_process_statuses_with_pending(self, mock_print):
        """Test processing statuses with pending ones"""
        statuses = [
            {'context': 'ci/test', 'state': 'success'},
            {'context': 'ci/build', 'state': 'pending'}
        ]
        
        all_complete, all_success, lines_printed = _process_statuses(statuses)
        
        assert all_complete is False
        assert all_success is True  # pending doesn't affect success flag
        assert lines_printed == 2
    
    @pytest.mark.unittest
    @patch('builtins.print')
    def test_process_statuses_with_failure(self, mock_print):
        """Test processing statuses with failures"""
        statuses = [
            {'context': 'ci/test', 'state': 'success'},
            {'context': 'ci/build', 'state': 'failure'}
        ]
        
        all_complete, all_success, lines_printed = _process_statuses(statuses)
        
        assert all_complete is True
        assert all_success is False
        assert lines_printed == 2
    
    @pytest.mark.unittest
    @patch('builtins.print')
    def test_process_statuses_empty_list(self, mock_print):
        """Test processing empty status list"""
        statuses = []
        
        all_complete, all_success, lines_printed = _process_statuses(statuses)
        
        assert all_complete is True
        assert all_success is True
        assert lines_printed == 0
        assert mock_print.call_count == 0
    
    @pytest.mark.unittest
    @patch('builtins.print')
    def test_process_statuses_missing_fields(self, mock_print):
        """Test processing statuses with missing fields"""
        statuses = [
            {'context': 'ci/test'},  # Missing state
            {'state': 'success'}     # Missing context
        ]
        
        all_complete, all_success, lines_printed = _process_statuses(statuses)
        
        assert lines_printed == 2
        mock_print.assert_any_call("   ❓ ci/test: [unknown]                                        ")
        mock_print.assert_any_call("   ✅ unknown: [success]                                        ")


if __name__ == '__main__':
    pytest.main([__file__])
