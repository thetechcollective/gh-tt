import json
import uuid

import pytest

from gh_tt.classes.config import Config
from gh_tt.tests.testbed import Testbed


@pytest.mark.integration
def test_workon_success():
    [owner, _] = Testbed.gitter_run(
        cmd='gh api user -H "X-Github-Next-Global-ID: 1" | jq -r .login'
    )
    
    repo_url, project_number = Testbed.create_github_resources(owner=owner)

    try:
        with Testbed.sandbox_repo(project_number=project_number, project_owner=owner) as repo:
            config = Config().config()
            Config().add_config(repo / ".tt-config.json")

            Testbed.gitter_run_all(cmds=[
                f'git remote add origin {repo_url}',
                'git push -u origin'
            ], cwd=repo)

            issue_url, _ = Testbed.gitter_run(
                cmd=f'gh issue create -R {repo_url} --title {uuid.uuid4().hex[:8]} --body ""',
            )

            # https://github.com/cli/cli/issues/11196
            issue_number = str(issue_url).split("/")[-1]

            Testbed.gitter_run(
                cmd=f'gh tt workon -i {issue_number} --verbose',
                cwd=repo
            )

            branch_name, _ = Testbed.gitter_run(
                cmd='git rev-parse --abbrev-ref HEAD',
                cwd=repo
            )

            issue_data, _ = Testbed.gitter_run(
                cmd=f'gh issue view -R {repo_url} {issue_number} --json assignees,body,closed,comments,labels,projectItems,projectCards,state'
            )
            issue = json.loads(issue_data)

            projects_data, _ = Testbed.gitter_run(
                cmd=f'gh project list --owner {owner} --format json --jq "[.projects[] | {{(.title): {{owner: .owner.login, number: .number}}}}] | add"'
            )
            projects = json.loads(projects_data)

            assert str(branch_name).startswith(issue_number), "Current branch is not prefixed with issue number"
            assert issue['assignees'][0]['login'] == owner, "Issue is not assigned"
            assert issue['projectItems'], "Issue is not connected to any project"
            assert not issue['closed'], "Issue is closed"

            assert any(
                config['workon']['default_type_labels']['issue'] == label['name'] 
                for label in issue['labels']
            ), "Issue does not have the workon label"

            assert any(
                config['project']['number'] == projects[item['title']]['number']
                and config['project']['owner'] == projects[item['title']]['owner']
                for item in issue['projectItems']
            ), "Issue is not connected to configured project"

            assert any(
                config['workon']['status'] == item['status']['name']
                for item in issue['projectItems']
            ), "Issue does not have a project item in the workon column"

    finally:
        Testbed.clean_up(repository_html_url=repo_url, project_number=project_number)