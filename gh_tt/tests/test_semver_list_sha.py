from unittest.mock import MagicMock

import pytest

from gh_tt.classes.semver import Semver, SemverTag


@pytest.mark.unittest
def test_semver_list_sha(capsys):
    """Test that list function shows SHA when show_sha is True"""
    # Setup
    mock_tags = "1.0.0\n1.0.1\nother-tag"
    mock_tag_shas = "abc123 1.0.0\ndef456 1.0.1\nghi789 other-tag"
    
    semver = Semver()
    semver.get = MagicMock(side_effect=lambda key: {
        'tags': mock_tags,
        'prefix': None,
        'tag_shas': mock_tag_shas,
        'semver_tags': semver._parse_tags(mock_tags, None, mock_tag_shas)
    }.get(key))

    # Test without SHA
    semver.list(filter_type='all')
    output = capsys.readouterr().out
    assert "1.0.0\n" in output
    assert "1.0.1\n" in output
    assert "other-tag\n" in output
    assert "abc123" not in output
    assert "def456" not in output

    # Test with SHA
    semver.list(filter_type='all', show_sha=True)
    output = capsys.readouterr().out
    assert "1.0.0 abc123\n" in output
    assert "1.0.1 def456\n" in output
    assert "other-tag" in output  # other-tag doesn't have a SemverTag object with SHA property

@pytest.mark.unittest
def test_semver_tag_with_sha():
    """Test that SemverTag can store SHA information"""
    from gh_tt.classes.semver import SemverVersion
    
    # Create a tag with SHA information
    version = SemverVersion(1, 0, 0)
    tag = SemverTag(version=version, sha="abc123")
    
    assert tag.sha == "abc123"
    assert str(tag) == "1.0.0"
