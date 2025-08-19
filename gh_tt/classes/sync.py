import asyncio
import json
import sys

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter


def get_sync_labels_commands(labels_to_sync: list[dict], sibling_repos: list[str]) -> set[str]:
    return {
        f"gh label create '{label['name']}' -R '{repo}' --color '{label['color']}' --description '{label['description']}' --force"
        for label in labels_to_sync
        for repo in sibling_repos
    }

async def sync_labels(config):
    [template_repo, _] = await Gitter(
        cmd="gh repo view --json nameWithOwner -q '.nameWithOwner'",
        msg="Get current repo name with owner"
    ).run()

    [labels_json, _] = await Gitter(
        cmd=f"gh label -R {template_repo} list --json name,description,color",
        msg='Get repo labels'
    ).run()

    labels = json.loads(labels_json)
    sibling_repos = config['sync']['sibling_repos']

    commands = get_sync_labels_commands(labels, sibling_repos)
    coroutines = {
        Gitter(
            cmd=command,
            msg='Create label'
        ).run()
        for command in commands
    }

    return await asyncio.gather(*coroutines, return_exceptions=True)

async def sync_milestones(config):
    [template_repo, _] = await Gitter(
        cmd="gh repo view --json nameWithOwner -q '.nameWithOwner'",
        msg="Get current repo name with owner"
    ).run()
    
    cmd = (
        'gh api '
        '-X GET '
        '-H "Accept: application/vnd.github+json" '
        '-H "X-GitHub-Api-Version: 2022-11-28" '
        '-f state=all '
        f'/repos/{template_repo}/milestones --paginate '
        "| jq 'map({title, description, due_on, state})'"
    )

    [data, _] = await Gitter(cmd=cmd, msg='Get milestones').run()
    milestones = json.loads(data)

    if not milestones:
        print('Template repository contains no milestones, so there is nothing to sync.')
        sys.exit(0)

    sibling_repos = config['sync']['sibling_repos']
    if not sibling_repos:
        print('Cannot sync milestones as there are no sibling repositories configured.', file=sys.stderr)
        sys.exit(1)

    commands = get_sync_milestones_commands(milestones, sibling_repos)
    coroutines = {
        Gitter(
            cmd=command,
            msg='Create milestone'
        ).run()
        for command in commands
    }

    return await asyncio.gather(*coroutines, return_exceptions=True)


def get_sync_milestones_commands(milestones_to_sync: list[dict], sibling_repos: list[str]) -> set[str]:
    assert sibling_repos
    assert milestones_to_sync
    
    commands = set()
    
    for milestone in milestones_to_sync:
        assert milestone.get('title') is not None

        for repo in sibling_repos:
            payload = {
                'title': milestone.get('title'),
                'state': milestone.get('state', 'open')
            }

            if milestone.get('description'):
                payload['description'] = milestone['description']

            if milestone.get('due_on'):
                payload['due_on'] = milestone['due_on']

            json_payload = json.dumps(payload)

            commands.add(
                f'gh api '
                f'-X POST '
                f'-H "Accept: application/vnd.github+json" '
                f'-H "X-GitHub-Api-Version: 2022-11-28" '
                f'/repos/{repo}/milestones '
                # Pass input in a shell-safe manner
                f'--input - <<\'EOF\'\n'
                f'{json_payload}\n'
                f'EOF'
            )

    return commands

def sync(*, labels: bool = False, milestones: bool = False):
    if labels:
        results = asyncio.run(sync_labels(config=Config.config()))

        successes = 0
        for result in results:
            if isinstance(result, RuntimeError):
                print(f"ERROR: A sync task failed:\n{result}", file=sys.stderr)
            elif isinstance(result, Exception):
                print(f"ERROR: An unexpected error occurred during sync:\n{result}", file=sys.stderr)
            else:
                successes += 1

        print(f"Sync complete: {successes}/{len(results)} tasks successful")

    if milestones:
        results = asyncio.run(sync_milestones(config=Config.config()))

        successes = 0
        for result in results:
            if isinstance(result, RuntimeError):
                print(f"ERROR: A sync task failed:\n{result}", file=sys.stderr)
            elif isinstance(result, Exception):
                print(f"ERROR: An unexpected error occurred during sync:\n{result}", file=sys.stderr)
            else:
                successes += 1

        print(f"Sync complete: {successes}/{len(results)} tasks successful")

