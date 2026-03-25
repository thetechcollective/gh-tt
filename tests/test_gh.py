from pytest_mock import MockerFixture

from gh_tt.commands import gh
from gh_tt.commands.shell import ShellResult


async def test_get_gh_auth_scopes_success(mocker: MockerFixture):
    result = """
    {
        "hosts": {
            "github.com": [
                {
                    "state": "success",
                    "active": true,
                    "host": "github.com",
                    "login": "vemolista",
                    "tokenSource": "/home/vscode/.config/gh/hosts.yml",
                    "scopes": "gist, project, read:org, repo, workflow",
                    "gitProtocol": "https"
                }
            ]
        }
    }
    """

    mocker.patch(
        'gh_tt.commands.shell.run',
        return_value=(ShellResult(result, mocker.Mock(), return_code=0)),
        new_callable=mocker.AsyncMock,
    )

    assert await gh.get_gh_auth_scopes() == ['gist', 'project', 'read:org', 'repo', 'workflow']
