import json
from pathlib import Path

import pytest
from pydantic import HttpUrl

from gh_tt import shell
from gh_tt.tests.env_builder import IntegrationEnv


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_basic_success():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        workon_result = await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        # Check branch name matches expected pattern
        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout
        assert branch_name.startswith(f'{env.issue_number}-')

        output = workon_result.stdout
        assert int(output.split('/')[-1]) == env.issue_number, (
            'Expected output url to end with the issue number'
        )
        assert HttpUrl(output), 'Expected output to be a valid url'

        # Verify a draft PR was created for this branch
        pr_data = await shell.run(
            [
                'gh',
                'pr',
                'view',
                branch_name,
                '-R',
                str(env.repo_url),
                '--json',
                'number,isDraft,body',
            ]
        )
        pr = json.loads(pr_data.stdout)

        assert pr['isDraft'], 'Expected PR to be a draft'
        assert f'#{env.issue_number}' in pr['body'], 'Expected PR body to reference the issue'


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_reuses_remote_branch():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        # First workon - creates the branch
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout

        # Make a commit so we can verify same branch is reused
        await shell.run(
            ['git', 'commit', '--allow-empty', '-m', 'marker commit'], cwd=env.local_repo
        )
        await shell.run(['git', 'push', '-u', 'origin', branch_name], cwd=env.local_repo)

        result = await shell.run(['git', 'rev-parse', 'HEAD'], cwd=env.local_repo)
        marker_sha = result.stdout

        # Switch back to main and delete local branch
        await shell.run(['git', 'checkout', 'main'], cwd=env.local_repo)
        await shell.run(['git', 'branch', '-D', branch_name], cwd=env.local_repo)

        # Run workon again - should reuse remote branch
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        # Verify we're on the same branch with the marker commit
        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        assert result.stdout == branch_name

        result = await shell.run(['git', 'rev-parse', 'HEAD'], cwd=env.local_repo)
        assert result.stdout == marker_sha


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_reuses_local_branch():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        # First workon - creates the branch
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        # Get the branch name
        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout.strip()

        # Make a marker commit
        await shell.run(
            ['git', 'commit', '--allow-empty', '-m', 'marker commit'], cwd=env.local_repo
        )
        result = await shell.run(['git', 'rev-parse', 'HEAD'], cwd=env.local_repo)
        marker_sha = result.stdout.strip()

        # Switch to main (local branch still exists)
        await shell.run(['git', 'checkout', 'main'], cwd=env.local_repo)

        # Run workon again - should switch to existing local branch
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        # Verify we're on the same branch with the marker commit
        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        assert result.stdout.strip() == branch_name

        result = await shell.run(['git', 'rev-parse', 'HEAD'], cwd=env.local_repo)
        assert result.stdout.strip() == marker_sha


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_with_project():
    workon_status_value = 'In Progress'

    async with (
        IntegrationEnv()
        .require_owner()
        .create_repo()
        .create_issue()
        .create_local_clone()
        .create_gh_project()
        .add_project_config(workon_status_value=workon_status_value)
        .build()
    ) as env:
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        assert isinstance(env.local_repo, Path), f'Expected type Path, got {type(env.local_repo)}'
        result = await shell.poll_until(
            [
                'gh',
                'project',
                'item-list',
                str(env.project_number),
                '--owner',
                str(env.owner),
                '--format',
                'json',
                '--jq',
                f'.items[] | select(.content.number == {env.issue_number})',
            ],
            cwd=env.local_repo,
            # given the jq filtering, we just want a non-empty result
            predicate=lambda r: r.stdout,
            timeout_seconds=15,
            interval=2,
        )

        if result is None:
            pytest.fail('Polling for project item timed out')

        project_item_data = json.loads(result.stdout)  # ty:ignore[possibly-missing-attribute] - we check the result above

        assert project_item_data is not None, 'Expected the project to have an item in progress'
        assert project_item_data['content']['number'] == env.issue_number
        assert project_item_data['content']['type'] == 'Issue'
        assert project_item_data['status'] == workon_status_value


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_commits_empty_with_pending_changes():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        await shell.run(
            ['echo', '"text"', '>', 'added.txt', '&&', 'git add added.txt'], cwd=env.local_repo
        )
        await shell.run(['echo', '"text"', '>', 'untracked.txt'], cwd=env.local_repo)

        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout

        # Verify new branch has one commit
        result = await shell.run(
            ['git', 'rev-list', '--count', f'main..{branch_name}'], cwd=env.local_repo
        )
        assert int(result.stdout) == 1

        # Verify new branch's commit is empty
        result = await shell.run(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'], cwd=env.local_repo
        )
        assert not result.stdout


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_title_success():
    async with IntegrationEnv().require_owner().create_repo().create_local_clone().build() as env:
        workon_result = await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-t', 'title of the issue', '--no-assign'],
            cwd=env.local_repo,
        )

        # Check branch name matches expected pattern
        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout

        issue_number = int(branch_name.split('-')[0])
        assert issue_number > 0, (
            f'Expected branch name to start with digits followed by a dash, instead got {branch_name}'
        )

        output = workon_result.stdout
        assert int(output.split('/')[-1]) == issue_number, (
            'Expected output url to end with the issue number'
        )
        assert HttpUrl(output), 'Expected output to be a valid url'

        # Verify a draft PR was created for this branch
        pr_data = await shell.run(
            [
                'gh',
                'pr',
                'view',
                branch_name,
                '-R',
                str(env.repo_url),
                '--json',
                'number,isDraft,body',
            ]
        )
        pr = json.loads(pr_data.stdout)

        assert pr['isDraft'], 'Expected PR to be a draft'
        assert f'#{issue_number}' in pr['body'], 'Expected PR body to reference the issue'
