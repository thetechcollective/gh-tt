import asyncio
import json
import sys
from dataclasses import dataclass

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter


@dataclass
class SyncResult:
    command: str
    success: bool
    error: str | None = None
    operation_type: str = ""
    target_repo: str = ""
    resource_name: str = ""


@dataclass
class SyncPlan:
    """Represents what sync operations to perform"""

    commands_with_metadata: list[tuple[str, dict]]
    template_repo: str
    sibling_repos: list[str]


def build_label_commands(
    labels: list[dict], sibling_repos: list[str], *, override_labels: bool
) -> list[tuple[str, dict]]:
    """Returns commands with context that should be executed to sync labels"""
    force_flag = " --force" if override_labels else ""

    commands = []
    for label in labels:
        for repo in sibling_repos:
            cmd = f"gh label create '{label['name']}' -R '{repo}' --color '{label['color']}' --description '{label['description']}'{force_flag}"
            metadata = {
                "operation_type": "label",
                "target_repo": repo,
                "resource_name": label["name"],
            }
            commands.append((cmd, metadata))
    return commands


def build_milestone_commands(
    milestones: list[dict], sibling_repos: list[str]
) -> list[tuple[str, dict]]:
    """Returns commands with context that should be executed to sync milestones"""
    commands = []

    for milestone in milestones:
        if not milestone.get("title"):
            continue

        for repo in sibling_repos:
            payload = {"title": milestone.get("title"), "state": milestone.get("state", "open")}

            if milestone.get("description"):
                payload["description"] = milestone["description"]

            if milestone.get("due_on"):
                payload["due_on"] = milestone["due_on"]

            json_payload = json.dumps(payload)

            cmd = f'gh api -X POST -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" /repos/{repo}/milestones --input - <<\'EOF\'\n{json_payload}\nEOF'

            metadata = {
                "operation_type": "milestone",
                "target_repo": repo,
                "resource_name": milestone["title"],
            }
            commands.append((cmd, metadata))

    return commands


def build_sync_plan(
    template_repo: str,
    sibling_repos: list[str],
    labels_data: list[dict] | None = None,
    milestones_data: list[dict] | None = None,
    *,
    override_labels: bool,
) -> SyncPlan:
    """Pure function: builds complete sync plan from inputs"""
    commands = []

    if labels_data:
        commands.extend(
            build_label_commands(labels_data, sibling_repos, override_labels=override_labels)
        )

    if milestones_data:
        commands.extend(build_milestone_commands(milestones_data, sibling_repos))

    return SyncPlan(
        commands_with_metadata=commands, template_repo=template_repo, sibling_repos=sibling_repos
    )


def categorize_results(results: list) -> tuple[list[SyncResult], list[str]]:
    """Pure function: categorizes execution results into successes and failures"""
    successes = []
    failures = []

    for result in results:
        if isinstance(result, Exception):
            failures.append(f"Unexpected error: {result}")
        elif isinstance(result, SyncResult):
            if result.success:
                successes.append(result)
            else:
                failures.append(
                    f"{result.operation_type} '{result.resource_name}' to {result.target_repo}: {result.error}"
                )
        else:
            failures.append(f"Unknown result type: {result}")

    return successes, failures


async def execute_with_metadata(cmd: str, metadata: dict) -> SyncResult:
    """Execute command and return structured result with context"""
    try:
        await Gitter(cmd=cmd).run()
        return SyncResult(
            command=cmd,
            success=True,
            operation_type=metadata["operation_type"],
            target_repo=metadata["target_repo"],
            resource_name=metadata["resource_name"],
        )
    except Exception as e:
        if metadata["operation_type"] == "label" and "already exists" in str(e):
            e = "label already exists"

        return SyncResult(
            command=cmd,
            success=False,
            error=str(e),
            operation_type=metadata["operation_type"],
            target_repo=metadata["target_repo"],
            resource_name=metadata["resource_name"],
        )


async def execute_sync_plan(
    plan: SyncPlan,
) -> list:
    """Execute a sync plan using provided executor function"""
    if not plan.commands_with_metadata:
        return []

    coroutines = [
        execute_with_metadata(cmd, metadata) for cmd, metadata in plan.commands_with_metadata
    ]
    return await asyncio.gather(*coroutines, return_exceptions=True)


async def fetch_template_data(
    template_repo: str, *, labels: bool = False, milestones: bool = False
) -> tuple[list[dict] | None, list[dict] | None]:
    """Fetch data from template repository. Returns a tuple of labels and milestones data."""
    labels_data = None
    milestones_data = None

    if labels:
        [labels_json, _] = await Gitter(
            cmd=f"gh label -R {template_repo} list --json name,description,color",
            msg="Get repo labels",
        ).run()
        labels_data = json.loads(labels_json)

    if milestones:
        [milestones_json, _] = await Gitter(
            cmd=(
                "gh api "
                "-X GET "
                '-H "Accept: application/vnd.github+json" '
                '-H "X-GitHub-Api-Version: 2022-11-28" '
                "-f state=all "
                f"/repos/{template_repo}/milestones --paginate "
                "| jq 'map({title, description, due_on, state})'"
            ),
            msg="Get milestones",
        ).run()
        milestones_data = json.loads(milestones_json)

    return labels_data, milestones_data


def sync(*, labels: bool = False, milestones: bool = False):
    """Main sync function - orchestrates the sync process"""
    config = Config.config()

    sibling_repos = config["sync"]["sibling_repos"]
    if not sibling_repos:
        print(
            "Cannot sync without sibling repositories. Set the sync:sibling_repos configuration value.",
            file=sys.stderr,
        )
        sys.exit(1)

    template_repo = config["sync"]["template_repo"]
    if not template_repo:
        print(
            "Cannot sync without a template repository. Set the sync:template_repo configuration value.",
            file=sys.stderr,
        )
        sys.exit(1)

    labels_data, milestones_data = asyncio.run(
        fetch_template_data(template_repo, labels=labels, milestones=milestones)
    )

    override_labels = config["sync"]["policies"]["override_labels"]
    plan = build_sync_plan(
        template_repo, sibling_repos, labels_data, milestones_data, override_labels=override_labels
    )
    if not plan.commands_with_metadata:
        return

    results = asyncio.run(execute_sync_plan(plan))
    successes, failures = categorize_results(results)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)

    if failures:
        print(f"Sync completed with errors: {len(successes)}/{len(results)} successful")
    elif successes:
        print(f"Sync completed: {len(successes)} operations successful")
