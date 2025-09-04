import pytest

from gh_tt.modules.tt_parser import tt_parse


@pytest.mark.unittest
def test_parser_semver_list_default():
    """Test that the parser defaults to 'all' filter for semver list"""
    args = ['semver', 'list']
    parsed = tt_parse(args)
    
    assert parsed.filter_type == 'all'
    assert parsed.semver_command == 'list'
    assert parsed.command == 'semver'


@pytest.mark.unittest
def test_parser_semver_list_with_filters():
    """Test that the parser accepts filter options for semver list"""
    filter_mapping = {
        '--release': 'release',
        '--prerelease': 'prerelease',
        '--pre': 'prerelease',  # Alias
        '--other': 'other',
        '--all': 'all'
    }
    
    for flag, expected in filter_mapping.items():
        args = ['semver', 'list', flag]
        parsed = tt_parse(args)
        
        assert parsed.filter_type == expected
        assert parsed.semver_command == 'list'
        assert parsed.command == 'semver'


@pytest.mark.unittest
def test_parser_semver_list_filter_mutual_exclusivity():
    """Test that the filter options are mutually exclusive"""
    # Combining two filter options should fail
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'list', '--release', '--prerelease'])
    
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'list', '--other', '--all'])
