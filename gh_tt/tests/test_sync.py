import json
from pathlib import Path

import pytest

from gh_tt.classes import sync


@pytest.mark.unittest
def test_get_sync_labels_commands():
    with Path.open(Path('gh_tt/tests/data/sync/gh_tt_labels.json')) as f:
        labels_to_sync = json.load(f)

    sibling_repos = ['owner/repo1', 'owner/repo2']

    commands = sync.get_sync_labels_commands(labels_to_sync=labels_to_sync, sibling_repos=sibling_repos)
    
    # Total number of commands matches product of labels and sibling repos
    assert len(commands) == len(labels_to_sync) * len(sibling_repos)
    # Commands are evenly distributed based on repo count
    assert len(commands) / len(sibling_repos) == len(labels_to_sync)

    # Each repo has the correct number of commands
    repo1_commands = sum(1 for command in commands if 'repo1' in command)
    repo2_commands = sum(1 for command in commands if 'repo2' in command)
    assert len(commands) / len(sibling_repos) == repo1_commands
    assert len(commands) / len(sibling_repos) == repo2_commands
