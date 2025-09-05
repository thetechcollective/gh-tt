import pytest

from gh_tt.modules.tt_parser import tt_parse


@pytest.mark.unittest
def test_parser_semver_list_sha_flag():
    """Test that the --sha flag is correctly parsed for semver list command"""
    
    # Test without --sha flag (default is False)
    args = tt_parse(['semver', 'list'])
    assert not args.sha
    
    # Test with --sha flag
    args = tt_parse(['semver', 'list', '--sha'])
    assert args.sha
    
    # Test with filter and sha
    args = tt_parse(['semver', 'list', '--release', '--sha'])
    assert args.sha
    assert args.filter_type == 'release'
