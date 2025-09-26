import argparse
import asyncio
import json
from datetime import date


async def main(since: date):  # noqa: C901
    # for all repositories that we care about
    # look for issues that have been closed in the past week
    # see if they have a label starting with f- or feat:
    # if not, group them by person and put the in a bulleted list ready to post in slack

    data = {
        "Arla OMB": [
            "Arla-OMB/omb-product",
            "Arla-OMB/python-new-dawn-graphql",
            "Arla-OMB/python-new-dawn-iac",
            "Arla-OMB/omb-frontend",
            "Arla-OMB/omb-e2e",
            "Arla-OMB/omb-cron",
        ],
        "CTS Risk Platform": [
            "thetechcollective/cts-risk-platform-frontend",
            "thetechcollective/cts-risk-platform-backend",
        ],
        "Internal Tooling": [
            "thetechcollective/gh-tt",
            "thetechcollective/gh-rotator",
            "thetechcollective/downstream-app",
            "thetechcollective/gh-set-status",
            "thetechcollective/gh-downstream",
        ],
    }

    tasks = []
    for items in data.values():
        for item in items:
            tasks.append(get_closed_issues(since, item))  # noqa: PERF401

    results = await asyncio.gather(*tasks)

    # Collect all issues from all repositories
    all_issues = []
    for repo_issues in results:
        if repo_issues:  # Skip None results from failed requests
            loaded = json.loads(repo_issues)
            all_issues.extend(loaded)

    print(f"Total issues found: {len(all_issues)}")

    # Group issues by assignee, filtering for those without feature labels
    issues_by_assignee = {}

    for issue in all_issues:
        # Check if issue has feature labels (starting with "f-" or "feat:")
        has_feature_label = any(
            label["name"].startswith("f-") or label["name"].startswith("feat:")
            for label in issue.get("labels", [])
        )

        if not has_feature_label:
            # Get all assignees for this issue
            assignees = issue.get("assignees", [])

            if not assignees:
                # Handle unassigned issues
                if "Unassigned" not in issues_by_assignee:
                    issues_by_assignee["Unassigned"] = []
                issues_by_assignee["Unassigned"].append(issue)
            else:
                # Add issue to each assignee's list
                for assignee in assignees:
                    # Use display name if available, otherwise fall back to login
                    name = assignee.get("name") or assignee["login"]
                    if name not in issues_by_assignee:
                        issues_by_assignee[name] = []
                    issues_by_assignee[name].append(issue)

    # Print results in Slack-ready format
    print("\n" + "=" * 50)
    print("Issues missing feature labels (f- or feat:):")
    print("=" * 50)

    for assignee, issues in issues_by_assignee.items():
        print(f"\n**{assignee}:**")
        for issue in issues:
            labels = ", ".join([label["name"] for label in issue.get("labels", [])])
            labels_text = f" (labels: {labels})" if labels else " (no labels)"
            print(f"• #{issue['number']}: {issue['url']}{labels_text}")

    if not issues_by_assignee:
        print("\n🎉 All recent issues have proper feature labels!")


async def get_closed_issues(since: date, repo: str):
    proc = await asyncio.create_subprocess_shell(
        f"gh issue ls -R {repo} -S 'closed:>{since.isoformat()}' --json assignees,number,url,labels",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        print(f"Error for {repo}: {stderr.decode()}")
        return None

    return stdout.decode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find issues missing feature labels")
    parser.add_argument(
        "--since",
        type=date.fromisoformat,
        required=True,
        help="Date to search from (YYYY-MM-DD format)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.since))
