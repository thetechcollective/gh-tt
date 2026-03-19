#!/usr/bin/env python3

from gh_tt.classes.semver import Semver


def test_note_from_to_args():
    """Test that the semver.note function accepts from_ref and to_ref arguments"""
    # Mock the note_md function to avoid git operations
    import unittest.mock as mock
    
    with mock.patch.object(Semver, 'note_md') as mock_note_md:
        mock_note_md.return_value = "Mock release note"
        
        # Create a Semver instance and mock methods/properties to avoid actual Git operations
        semver = Semver()
        
        # Mock the get method to return dummy data
        mock_tags = {'current': {'release': ['0.9.0', '1.0.0'], 'prerelease': ['1.0.0-rc1']}}
        # Use a single with statement with multiple contexts
        with mock.patch.object(semver, 'get', return_value=mock_tags), \
             mock.patch.object(semver, 'get_current_semver') as mock_get_semver:
            mock_get_semver.side_effect = lambda release_type=None: "1.0.0" if release_type is None else "1.0.0-rc1"
            
            # Test with explicit from_ref and to_ref
            semver.note(from_ref="0.9.0", to_ref="1.0.0")
            
            # Verify note_md was called with correct arguments
            mock_note_md.assert_called_with(from_ref="0.9.0", to_ref="1.0.0")
            
            # Test with default values (should use get_current_semver)
            semver.note()
            
            # Should have used default behavior for determining refs
            assert mock_note_md.call_count >= 2
            
            # Verify the last call used the default behavior
            last_call_args = mock_note_md.call_args
            assert last_call_args[1]['from_ref'] == '0.9.0'  # Should be previous release
            assert last_call_args[1]['to_ref'] == '1.0.0'    # Should be current release
