import asyncio
import os
import sys

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

from lazyload import Lazyload

class Version(Lazyload):
    async def __init__(self):
        super().__init__()

        installed_gh_extensions = await self._run("extension_list")
        sha = self._get_gh_tt_sha(extension_list=installed_gh_extensions)
        self.set("sha", sha)

        raw_tags = await self._run("sha_tags")
        self.set("tags", self._get_tags(raw_tags=raw_tags))



    def print(self):
        print("gh-tt extension")
        print(f"Version SHA: {self.get("sha")}")
        print(f"Version tags: {self.get("tags")}")

    def _get_gh_tt_sha(self, extension_list: str) -> str:
        lines = extension_list.splitlines()
        
        sha = None
        for line in lines:
            if line.startswith("gh tt"):
                parts = line.split("\t")
                sha = parts[2]
                break

        if not sha:
            print("🛑  SHA for current gh tt version could not be extracted from gh extension list")
            sys.exit(1)

        return sha

    def _get_tags(self, raw_tags: str) -> str:
        return ", ".join(raw_tags.split("\n") if raw_tags != "" else "The current SHA has no tags attached")
