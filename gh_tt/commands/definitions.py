import json
from typing import Any

from gh_tt.commands.command import Command

BRANCH_NAME = Command(
    name="branch_name",
    command="git rev-parse --abbrev-ref HEAD",
    description="Get the name of the current branch",
)

SHA1 = Command(
    name="sha1",
    command="git rev-parse HEAD",
    description="Get the SHA1 of the current branch",
)

STATUS = Command(
    name="status",
    command="git status --porcelain",
    description="Get the status of the working directory",
)

REMOTE = Command(
    name="remote",
    command="git remote",
    description="Get the name of the remote",
)

DEFAULT_BRANCH = Command(
    name="default_branch",
    command="gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'",
    description="Get the name of the default branch from GitHub",
)


def parse_issue_all(raw: str) -> dict[str, Any]:
    data = json.loads(raw)

    return {
        "issue_url": data["url"],
        "issue_title": data["title"],
        "issue_number": data["number"],
        "issue_labels": data["labels"],
        "issue_assignees": data["assignees"],
        "issue_closed": data["closed"],
        "issue_comments": data["comments"],
    }


ISSUE = Command(
    name="issue_all",
    description="Get properties from an issue",
    command="gh issue view {number} --json url,title,number,labels,assignees,closed,comments",
    params={"number": int},
    outputs=(
        "issue_url",
        "issue_title",
        "issue_number",
        "issue_labels",
        "issue_assignees",
        "issue_closed",
        "issue_comments",
    ),
    parser=parse_issue_all,
)


ALL_COMMANDS = [BRANCH_NAME, SHA1, STATUS, REMOTE, DEFAULT_BRANCH, ISSUE]
