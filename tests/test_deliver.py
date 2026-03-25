from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import provisional as hypothesis_provisional
from hypothesis import strategies as st
from pydantic import HttpUrl

from gh_tt import shell
from gh_tt.commands import gh
from gh_tt.commands.gh import Commit
from gh_tt.commands.git import PR_START_COMMIT_HEADLINE
from gh_tt.deliver import _build_merge_body
from tests.env_builder import IntegrationEnv

st.register_type_strategy(HttpUrl, hypothesis_provisional.urls().map(HttpUrl))


@given(pr=st.from_type(gh.PullRequest))
def test_merge_body_no_crash(pr: gh.PullRequest):
    _build_merge_body(pr)


@given(pr=st.from_type(gh.PullRequest))
def test_merge_body_does_not_include_skip_ci_in_first_commit(pr: gh.PullRequest):
    pr.commits = [gh.Commit(messageHeadline=PR_START_COMMIT_HEADLINE, messageBody='')]
    body = _build_merge_body(pr)

    assert '[skip ci]' not in body


@given(pr=st.from_type(gh.PullRequest).filter(lambda pr: len(pr.commits) > 1))
def test_merge_body_includes_skip_ci_outside_of_first_commit(pr: gh.PullRequest):
    pr.commits[1] = Commit(messageHeadline=PR_START_COMMIT_HEADLINE, messageBody='')

    body = _build_merge_body(pr)
    assert '[skip ci]' in body


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_deliver_flow_success():
    async with (
        IntegrationEnv().require_owner().create_repo().create_issue().create_local_clone().build()
    ) as env:
        assert isinstance(env.local_repo, Path), f'Expected type Path, got {type(env.local_repo)}'

        # Arrange
        await shell.run(
            ['gh', 'tt', 'workon', '--pr-workflow', '-i', str(env.issue_number), '--no-assign'],
            cwd=env.local_repo,
        )

        result = await shell.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=env.local_repo)
        branch_name = result.stdout

        result = await shell.poll_until(
            ['gh', 'pr', 'view', branch_name, '--json', 'number', '--jq', '.number'],
            cwd=env.local_repo,
            predicate=lambda r: bool(r.stdout),
        )
        assert result is not None, 'Expected PR to be created'
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

        result = await shell.poll_until(
            ['gh', 'pr', 'view', str(pr_number), '--json', 'mergedAt', '--jq', '.mergedAt'],
            cwd=env.local_repo,
            predicate=lambda r: bool(r.stdout),
        )
        assert result is not None, 'Expected PR to be merged'

        output = deliver_result.stdout
        assert int(output.split('/')[-1]) == int(pr_number), (
            'Expected output url to end with the PR number'
        )
        assert HttpUrl(output), 'Expected output to be a valid url'

        merge_commit = await shell.run(
            [
                'gh',
                'pr',
                'view',
                str(pr_number),
                '--json',
                'mergeCommit',
                '--jq',
                '.mergeCommit.oid',
            ],
            cwd=env.local_repo,
        )
        await shell.run(
            ['git', 'fetch', 'origin', 'main'],
            cwd=env.local_repo,
        )
        commit_body = await shell.run(
            ['git', 'log', '-1', '--format=%b', merge_commit.stdout],
            cwd=env.local_repo,
        )
        assert '[skip ci]' not in commit_body.stdout, (
            'Expected merge commit body to not contain [skip ci]'
        )


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_deliver_fails_when_not_up_to_date_with_default_branch():
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

        await shell.run(['git', 'switch', 'main'], cwd=env.local_repo)
        await shell.run(
            ['git', 'commit', '-m', 'main is ahead', '--allow-empty'], cwd=env.local_repo
        )
        await shell.run(['git', 'push', 'origin', 'main'], cwd=env.local_repo)
        await shell.run(['git', 'switch', branch_name], cwd=env.local_repo)

        # Act
        result = await shell.run(
            ['gh', 'tt', 'deliver', '--pr-workflow', '--delete-branch'],
            cwd=env.local_repo,
            die_on_error=False,
        )

        # Assert
        assert result.return_code == 1
        assert 'branch has commits your branch does not' in result.stderr

        pr_result = await shell.run(
            [
                'gh',
                'pr',
                'view',
                branch_name,
                '--json',
                'state,autoMergeRequest',
                '--jq',
                '{state, autoMergeRequest}',
            ],
            cwd=env.local_repo,
        )
        assert '"state":"OPEN"' in pr_result.stdout.replace(' ', ''), 'Expected PR to still be open'
        assert '"autoMergeRequest":null' in pr_result.stdout.replace(' ', ''), (
            'Expected PR to not have auto-merge enabled'
        )


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_deliver_fails_when_local_ahead_of_remote():
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

        await shell.run(
            ['git', 'commit', '-m', 'local is ahead', '--allow-empty'], cwd=env.local_repo
        )

        # Act
        result = await shell.run(
            ['gh', 'tt', 'deliver', '--pr-workflow', '--delete-branch'],
            cwd=env.local_repo,
            die_on_error=False,
        )

        # Assert
        assert result.return_code == 1
        assert 'is not up to date with its remote' in result.stderr

        pr_result = await shell.run(
            [
                'gh',
                'pr',
                'view',
                branch_name,
                '--json',
                'state,autoMergeRequest',
                '--jq',
                '{state, autoMergeRequest}',
            ],
            cwd=env.local_repo,
        )
        assert '"state":"OPEN"' in pr_result.stdout.replace(' ', ''), 'Expected PR to still be open'
        assert '"autoMergeRequest":null' in pr_result.stdout.replace(' ', ''), (
            'Expected PR to not have auto-merge enabled'
        )


@pytest.mark.usefixtures('check_end_to_end_env')
async def test_workon_deliver_fails_when_local_behind_remote():
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

        # Push a commit to the remote and remove it from the local branch
        await shell.run(
            ['git', 'commit', '-m', 'remote is ahead', '--allow-empty'], cwd=env.local_repo
        )
        await shell.run(['git', 'push', '-u', 'origin', branch_name], cwd=env.local_repo)
        await shell.run(['git', 'reset', '--hard', 'HEAD~1'], cwd=env.local_repo)

        # Act
        result = await shell.run(
            ['gh', 'tt', 'deliver', '--pr-workflow', '--delete-branch'],
            cwd=env.local_repo,
            die_on_error=False,
        )

        # Assert
        assert result.return_code == 1
        assert 'is not up to date with its remote' in result.stderr

        pr_result = await shell.run(
            [
                'gh',
                'pr',
                'view',
                branch_name,
                '--json',
                'state,autoMergeRequest',
                '--jq',
                '{state, autoMergeRequest}',
            ],
            cwd=env.local_repo,
        )
        assert '"state":"OPEN"' in pr_result.stdout.replace(' ', ''), 'Expected PR to still be open'
        assert '"autoMergeRequest":null' in pr_result.stdout.replace(' ', ''), (
            'Expected PR to not have auto-merge enabled'
        )
