from enum import Enum
from project import Project
from lazyload import Lazyload
from gitter import Gitter
import os
import sys
import re
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

class IssueType(Enum):
    DOCUMENTATION = 'Documentation'
    DEV_TASK = 'Dev Task'
    AD_HOC = 'Ad Hoc'
    BUG_FIX = 'Bug Fix'
    FEATURE = 'Feature'
    FUNCTIONAL_TEST = 'Functional Test'
    INFRASTRUCTURE = 'Infrastructure'
    REFACTOR = 'Refactor'
    UNIT_TEST = 'Unittest'
    USER_STORY_ARLA = 'User Story (Arla)'

    @classmethod
    def from_str(cls, issue_type: str):
        if not isinstance(issue_type, str):
            raise AttributeError(f"Issue type must be string, instead got {type(issue_type)}")

        mapping = {
            'ad_hoc': cls.AD_HOC,
            'bug_fix': cls.BUG_FIX,
            'dev_task': cls.DEV_TASK,
            'documentation': cls.DOCUMENTATION,
            'feature': cls.FEATURE,
            'functional_test': cls.FUNCTIONAL_TEST,
            'infrastructure': cls.INFRASTRUCTURE,
            'refactor': cls.REFACTOR,
            'unittest': cls.UNIT_TEST,
            'user_story_arla': cls.USER_STORY_ARLA
        }

        result = mapping.get(issue_type)

        if result is None:
            raise ValueError(f"Unknown issue type: {issue_type}")

        return mapping.get(issue_type)


class Issue(Lazyload):
    """Class used to represent a GitHub issue - in context of the current development branch"""

    def __init__(self, number: int, issue_type: str | IssueType | None = None):
        super().__init__()

        if isinstance(issue_type, str):
            issue_type = IssueType.from_str(issue_type)

        self.set('number', number)
        self.set('issue_type', issue_type)
        self.set('url', None)
        self.set('title', None)
        self.set('item_id', None)
        self.set('assignee', None)

        result = None
        gitter = Gitter(
            cmd=f"gh api -H \"Accept: application/vnd.github+json\" /repos/:owner/:repo/issues/{number} | jq '{{url: .html_url, title, type: .type.name}}'"
        )
        [output, result] = gitter.run()
        if result.returncode != 0:
            print(
                f"ERROR: Issue '{number}' doesn't exit in current git context\n{result.stderr}", file=sys.stderr)
            exit(1)

        # the output looks like:
        # {
        #   "title": "Refactor",
        #   "url": "https://github.com/thetechcollective/gh-tt/issues/26"
        #   "type": "Documentation"
        # }

        try:
            issue_json = json.loads(output)
        except ValueError as e:
            pass
            print(
                f"ERROR: Could not get the issue url or title on issue number: '{number}'\n{result.stderr}", file=sys.stderr)
            exit(1)

        self.set('url', issue_json.get('url'))
        self.set('title', issue_json.get('title'))

        if self.get('url') is None or self.get('title') is None:
            print(
                f"ERROR: Could not get the issue url or title from incomplete JSON:\n{issue_json}", file=sys.stderr)
            exit(1)

        if self.get('issue_type') is None and issue_json.get('type') is None:
            print(
                f"ERROR: Issue type is not set, and no issue type was passed via the --type argument.\nissue_json: {issue_json}\ntype argument: {issue_type}\n\nTo set the issue type, use the --type argument.", file=sys.stderr)
            exit(1)

        if self.get('issue_type') is not None and self.get('issue_type').value != issue_json.get('type'):
            gitter = Gitter(
                cmd=f"gh api --method PATCH -H \"Accept: application/vnd.github+json\" /repos/:owner/:repo/issues/{number} -f \"type={self.get('issue_type').value}\" | jq '{{url: .html_url, title, type: .type.name}}'"
            )
            [output, result] = gitter.run()

            if result.returncode != 0:
                print(
                    f"ERROR: Could not update the issue type for issue #{number}.\n{result.stderr}", file=sys.stderr)
                exit(1)


    @classmethod
    def create_new(cls, title=str, issue_type=str, body=None):
        """Create a new issue on the current repository
        Works as an alternative to the constructor, call it on the class and it will return a new Issue object

        Args:
            title (str): The title of the issue (required)
            issue_type (str): Issue type of the issue (required)
            body (str): The body of the issue (defaults to None)
        """

        body_switch = f"-f \"body={body}\"" if body is not None else ""
        issue_type = IssueType.from_str(issue_type)

        gitter = Gitter(
            cmd=f"gh api --method POST -H \"Accept: application/vnd.github+json\" /repos/:owner/:repo/issues -f \"title={title}\" {body_switch} -f \"type={issue_type.value}\" | jq '{{url: .html_url, title, type: type.name}}'",
            msg="Create a new issue"
        )
        [output, result] = gitter.run()

        # the output looks like:
        # {
        #   "title": "Refactor",
        #   "url": "https://github.com/thetechcollective/gh-tt/issues/26"
        #   "type": "Documentation"
        # }

        issue_url = re.search(r'(https://github.com/.*/issues/\d+)', output)
        if issue_url:
            issue_number = issue_url.group(1).split('/')[-1]
        else:
            print(
                f"ERROR: Could not capture the issue URL from the output:\n{output}", file=sys.stderr)
            exit(1)

        return cls(number=issue_number, issue_type=issue_type)

    def add_to_project(self, owner=str, number=int):
        """Add the issue to a project column"""

        if self.get('item_id') is not None:
            return self.get('item_id')

        url = self.get('url')
        gitter = Gitter(
            cmd=f"gh project item-add {number}  --owner {owner} --url {url} --format json --jq '.id'",
            die_on_error=False,
            msg="Add the issue to a project column")
        [item_id, result] = gitter.run()

        if result.returncode != 0:
            print(
                f"ERROR: Could not add the issue to the project {owner}/{number}\n{result.stderr}", file=sys.stderr)
            exit(1)

        self.set('item_id', item_id)

        return item_id

    def assign(self, assignee=str):
        """Assign the issue to a user"""

        issue_number = self.get('number')

        [output, result] = Gitter(
            cmd=f"gh issue edit {issue_number} --add-assignee '{assignee}'",
            msg=f"Assign @me to the issue").run()

        self.set('assignee', assignee)
        return output
