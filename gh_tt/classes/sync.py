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


def sync(*, labels: bool = False):
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

