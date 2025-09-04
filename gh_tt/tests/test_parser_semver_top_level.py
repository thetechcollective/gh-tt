import pytest

from gh_tt.modules.tt_parser import tt_parse


@pytest.mark.unittest
def test_parser_semver_top_level_default():
    """Test that the parser defaults to showing release versions at the top level"""
    args = ['semver']
    parsed = tt_parse(args)
    
    assert parsed.prerelease is False
    assert parsed.command == 'semver'
    assert parsed.semver_command is None


@pytest.mark.unittest
def test_parser_semver_top_level_with_prerelease():
    """Test that the parser accepts --prerelease at the top level"""
    # Test both --prerelease and its alias --pre
    for flag in ['--prerelease', '--pre']:
        args = ['semver', flag]
        parsed = tt_parse(args)
        
        assert parsed.prerelease is True
        assert parsed.command == 'semver'
        assert parsed.semver_command is None
