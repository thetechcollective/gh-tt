import json

from async_lru import alru_cache
from pydantic import AliasPath, BaseModel, Field

from gh_tt import shell


class Repo(BaseModel):
    name: str = Field(alias='nameWithOwner')
    default_branch: str = Field(alias=AliasPath('defaultBranchRef', 'name'))

@alru_cache
async def get_repo() -> Repo:
    result = await shell.run(['gh', 'repo', 'view', '--json', 'nameWithOwner,defaultBranchRef'])
    
    return Repo(**json.loads(result.stdout))