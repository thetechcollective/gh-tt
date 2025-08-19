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