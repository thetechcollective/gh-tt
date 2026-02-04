import json
import re

from async_lru import alru_cache
from pydantic import BaseModel, Field, HttpUrl, PositiveInt

from gh_tt import shell


class Label(BaseModel):
    identifier: str = Field(alias='id', pattern=r'^LA')
    name: str
    description: str = Field(max_length=100)
    color: str = Field(min_length=6, max_length=6)

class Assignee(BaseModel):
    identifier: str = Field(alias='id')
    login: str
    name: str

class Issue(BaseModel):
    url: HttpUrl
    title: str
    number: PositiveInt
    labels: list[Label]
    assignees: list[Assignee]
    closed: bool

@alru_cache
async def get_issue(issue_number: int) -> Issue:
    result = await shell.run(cmd=['gh', 'issue', 'view', str(issue_number), '--json', 'url,title,number,labels,assignees,closed'])

    return Issue(**json.loads(result.stdout))

async def develop_issue(issue_title: str, issue_number: int, default_branch: str) -> str:
    sanitized_title = re.sub(r'[^a-zA-Z0-9]+', '_', issue_title)
    branch_name = f'{issue_number}-{sanitized_title}'

    await shell.run(cmd=['gh', 'issue', 'develop', str(issue_number), '--base', default_branch, '--name', branch_name, '--checkout'])

    return branch_name

async def assign_issue(issue_number: int, assignee: str):
    await shell.run(cmd=['gh', 'issue', 'edit', str(issue_number), '--add-assignee', assignee])