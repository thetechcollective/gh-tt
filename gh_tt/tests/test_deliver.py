from pathlib import Path

import pytest
from pydantic import HttpUrl

from gh_tt import shell
from gh_tt.tests.env_builder import IntegrationEnv


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_deliver_flow_success():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        # Arrange
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout

        result = await shell.run(
            ['gh', 'pr', 'view', branch_name, '--json', 'number', '--jq', '.number'],
            cwd=env.local_repo,
        )
        pr_number = result.stdout

        # Act
        deliver_result = await shell.run(
            ['gh', 'tt', 'deliver', '--pr-workflow', '--delete-branch'], cwd=env.local_repo
        )

        # Assert
        result = await shell.run(
            ['git', 'ls-remote', '--heads', 'origin', branch_name], cwd=env.local_repo
        )
        assert not result.stdout, f'Expected remote branch {branch_name} to be deleted'

        assert isinstance(env.local_repo, Path), f'Expected type Path, got {type(env.local_repo)}'
        result = await shell.poll_until(
            ['gh', 'pr', 'view', str(pr_number), '--json', 'mergedAt', '--jq', '.mergedAt'],
            cwd=env.local_repo,
            predicate=lambda r: bool(r.stdout),
            timeout_seconds=15,
            interval=3,
        )
        assert result is not None, 'Expected PR to be merged'

        output = deliver_result.stdout
        assert int(output.split('/')[-1]) == int(pr_number), (
            'Expected output url to end with the PR number'
        )
        assert HttpUrl(output), 'Expected output to be a valid url'
