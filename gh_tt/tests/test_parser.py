import pytest

from gh_tt.modules.tt_parser import tt_parse


@pytest.mark.unittest
@pytest.mark.parametrize('args', [['sync'], ['sync', '--gibberish']])
def test_parser_sync_entity_required(args):
    """Parser raises when no entity to sync (e.g. --labels) is passed"""

    with pytest.raises(SystemExit):
        tt_parse(args)

@pytest.mark.unittest
@pytest.mark.parametrize('entity', ['--labels', '--milestones'])
def test_parser_sync_success(entity):
    args = ['sync', entity]

    tt_parse(args)

@pytest.mark.unittest
def test_parser_semver_bump_prerelease():
    """Test that the parser accepts the --pre option for prerelease bump"""
    args = ['semver', 'bump', '--pre']
    parsed = tt_parse(args)
    
    assert parsed.level == 'prerelease'
    assert parsed.semver_command == 'bump'
    assert parsed.command == 'semver'

@pytest.mark.unittest
def test_parser_semver_bump_build():
    """Test that the parser accepts the --build option for build bump"""
    args = ['semver', 'bump', '--build']
    parsed = tt_parse(args)
    
    assert parsed.level == 'build'
    assert parsed.semver_command == 'bump'
    assert parsed.command == 'semver'
    assert parsed.include_sha is True  # Default is to include SHA

@pytest.mark.unittest
def test_parser_semver_bump_build_no_sha():
    """Test that the parser accepts the --build option with --no-sha"""
    args = ['semver', 'bump', '--build', '--no-sha']
    parsed = tt_parse(args)
    
    assert parsed.level == 'build'
    assert parsed.include_sha is False
    assert parsed.semver_command == 'bump'
    assert parsed.command == 'semver'

@pytest.mark.unittest
def test_parser_semver_bump_with_prefix():
    """Test that the parser accepts the --prefix option with any bump level"""
    level_mapping = {
        '--major': 'major',
        '--minor': 'minor',
        '--patch': 'patch',
        '--pre': 'prerelease',
        '--build': 'build'
    }
    
    for flag, expected in level_mapping.items():
        args = ['semver', 'bump', flag, '--prefix', 'v']
        parsed = tt_parse(args)
        
        assert parsed.prefix == 'v'
        assert parsed.level == expected
        assert parsed.semver_command == 'bump'
        assert parsed.command == 'semver'

@pytest.mark.unittest
def test_parser_semver_bump_with_message():
    """Test that the parser accepts the -m/--message option with any bump level"""
    message = "Test release message"
    args = ['semver', 'bump', '--major', '-m', message]
    parsed = tt_parse(args)
    
    assert parsed.message == message
    assert parsed.level == 'major'
    assert parsed.semver_command == 'bump'
    assert parsed.command == 'semver'

@pytest.mark.unittest
def test_parser_semver_bump_with_run_options():
    """Test that the parser accepts --run and --no-run options"""
    # Default behavior (no run flag specified)
    args = ['semver', 'bump', '--major']
    parsed = tt_parse(args)
    assert parsed.run is True
    
    # Explicit run flag
    args = ['semver', 'bump', '--major', '--run']
    parsed = tt_parse(args)
    assert parsed.run is True
    
    # No-run flag
    args = ['semver', 'bump', '--major', '--no-run']
    parsed = tt_parse(args)
    assert parsed.run is False

@pytest.mark.unittest
def test_parser_semver_bump_mutual_exclusivity():
    """Test that the level options are mutually exclusive"""
    # Combining two level options should fail
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'bump', '--major', '--minor'])
    
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'bump', '--pre', '--build'])

@pytest.mark.unittest
def test_parser_semver_bump_level_required():
    """Test that a level option is required"""
    # Missing required level argument
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'bump'])

@pytest.mark.unittest
def test_parser_semver_bump_build_options():
    """Test that build-specific options work correctly"""
    # Test default (include SHA)
    args = ['semver', 'bump', '--build']
    parsed = tt_parse(args)
    assert parsed.level == 'build'
    assert parsed.include_sha is True
    
    # Test --no-sha
    args = ['semver', 'bump', '--build', '--no-sha']
    parsed = tt_parse(args)
    assert parsed.level == 'build'
    assert parsed.include_sha is False
    
    # Test that --no-sha cannot be used with other levels
    with pytest.raises(SystemExit):
        tt_parse(['semver', 'bump', '--major', '--no-sha'])