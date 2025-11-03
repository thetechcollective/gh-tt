import json
import os
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import NamedTuple

import pytest

from gh_tt.classes.config import Config, LoadStrategy
from gh_tt.classes.gitter import Gitter
from gh_tt.tests.testbed import Testbed


class FixtureReturn(NamedTuple):
    owner: str
    config: dict
    github_repo_url: str
    local_repo_path: Path
    issue_number: int
    project_number: int


def query_github_org_name_from_id(github_org_id: str):
    return f"""
        gh api graphql -f query='query {{
            node(id: "{github_org_id}") {{
                ... on Organization {{
                    name
                }}
            }}
        }})'
    """

@pytest.fixture
def workon_success_env() -> Generator[FixtureReturn]:
    owner = None
    if os.getenv("GH_TOKEN") is not None:
        qa_org_id = os.getenv("QA_ORGANIZATION_ID")
        assert qa_org_id is not None, "QA_ORGANIZATION_ID environment variable is not set"

        [owner_data, _] = Testbed.gitter_run(cmd=query_github_org_name_from_id(qa_org_id))
        owner = json.loads(owner_data)['data']['node']['name']
    else:
        [extension_list, _] = Testbed.gitter_run(cmd='gh extension list')
        if 'thetechcollective/gh-tt' in extension_list:
            raise SystemExit(
                "You have a remote version of the 'gh-tt' extension installed.\n"
                "Your local changes would not be taken into consideration when running the integration test.\n"
                "Remove the existing extension with `gh extension remove gh-tt`, then \n"
                "install the local version with `gh extension install .`"
            )

        try:
            Gitter.validate_gh_scope('repo')
            Gitter.validate_gh_scope('project')
            Gitter.validate_gh_scope('delete_repo')
        except SystemExit as e:
            raise SystemExit("The gh scopes 'repo', 'project' and 'delete_repo' are required to run the integration test outside of GitHub Actions.") from e

        [owner, _] = Testbed.gitter_run(cmd='gh api user -H "X-Github-Next-Global-ID: 1" | jq -r .login')

    assert owner is not None, "Owner is required for running integration tests"

    repo_url = Testbed.create_github_repository(owner)
    project_number = Testbed.create_github_project(owner)

    issue_url, _ = Testbed.gitter_run(
        cmd=f'gh issue create -R {repo_url} --title {uuid.uuid4().hex[:8]} --body ""',
    )
    issue_number = str(issue_url).split("/")[-1]

    with Testbed.create_local_repo() as local_repo_path:
        (local_repo_path / ".tt-config.json").write_text(json.dumps({"project": {"owner": owner, "number": project_number}}, indent=4))
        config = Config().config(load_only_default=LoadStrategy.ONLY_DEFAULT_CONFIG)
        Config().add_config(local_repo_path / ".tt-config.json")
        Testbed.gitter_run_all([f"git remote add origin {repo_url}", "git add .", 'git commit -m "add config"', "git push -u origin HEAD"], cwd=local_repo_path)

        yield FixtureReturn(local_repo_path=local_repo_path, github_repo_url=repo_url, owner=owner, issue_number=issue_number, config=config, project_number=project_number)

    Testbed.clean_up(repository_html_url=repo_url, project_number=project_number, project_owner=owner)


@pytest.mark.integration
def test_workon_success(workon_success_env):
    env = workon_success_env

    Testbed.gitter_run(cmd=f"gh tt workon -i {env.issue_number} --verbose --no-assign", cwd=env.local_repo_path)

    branch_name, _ = Testbed.gitter_run(cmd="git rev-parse --abbrev-ref HEAD", cwd=env.local_repo_path)

    issue_data, _ = Testbed.gitter_run(
        cmd=f"gh issue view -R {env.github_repo_url} {env.issue_number} --json assignees,body,closed,comments,labels,projectItems,state"
    )
    issue = json.loads(issue_data)

    projects_data, _ = Testbed.gitter_run(
        cmd=f'gh project list --owner {env.owner} --format json --jq "[.projects[] | {{(.title): {{owner: .owner.login, number: .number}}}}] | add"'
    )
    projects = json.loads(projects_data)

    assert str(branch_name).startswith(env.issue_number), "Current branch is not prefixed with issue number"
    assert issue["projectItems"], "Issue is not connected to any project"
    assert not issue["closed"], "Issue is closed"

    assert any(env.config["workon"]["default_type_labels"]["issue"] == label["name"] for label in issue["labels"]), "Issue does not have the workon label"

    assert any(
        int(env.config["project"]["number"]) == projects[item["title"]]["number"] and env.config["project"]["owner"] == projects[item["title"]]["owner"]
        for item in issue["projectItems"]
    ), "Issue is not connected to configured project"

    assert any(env.config["workon"]["status"] == item["status"]["name"] for item in issue["projectItems"]), "Issue does not have a project item in the workon column"