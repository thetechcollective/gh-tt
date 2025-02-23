from project import Project
from lazyload import Lazyload
from gitter import Gitter
import os
import subprocess
import sys
import re
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Issue(Lazyload):
    """Class used to represent a GitHub issue - in context of the current development branch"""

    def __init__(self, number=int):
        super().__init__()

        self.set('number', number)
        self.set('url', None)
        self.set('title', None)
        self.set('item_id', None)
        self.set('assignee', None)

        result = None
        gitter = Gitter(
            cmd=f"gh issue view {number} --json url,title",
            msg="Get the url and title from the issue",
            die_on_error=False)
        [output, result] = gitter.run()
        if result.returncode != 0:
            print(
                f"ERROR: Issue '{number}' doesn't exit in current git context\n{result.stderr}", file=sys.stderr)
            exit(1)

        # the output looks like:
        # {
        #   "title": "Refactor",
        #   "url": "https://github.com/thetechcollective/gh-tt/issues/26"
        # }
        # Load the json and set the url and title

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

    @classmethod
    def create_new(cls, title=str, body=None, assign=None):
        """Create a new issue on the current repository
        Works as an alternative to the constructor, call it on the class and it will return a new Issue object

        Args:
            title (str): The title of the issue (required)
            body (str): The body of the issue  (defaults to None)
            assign: Assign to the issue (defaults to the current user)
        """

        body_switch = f"--body '{body}'" if body is not None else "--body ''"
        assign_switch = f"--assignee '{assign}'" if assign is not None else ""

        gitter = Gitter(
            cmd=f"gh issue create --title '{title}' {body_switch} {assign_switch}",
            msg="Create a new issue")
        [output, result] = gitter.run()

        # The output is a mulitiline string like this:
        #
        #   Creating issue in lakruzz/gitsquash_lab
        #
        #   https://github.com/lakruzz/gitsquash_lab/issues/15

        # Capture the url of the issue and set it on the object
        # and capture the issue number from the tail of the url and set it on the object

        issue_url = re.search(r'(https://github.com/.*/issues/\d+)', output)
        if issue_url:
            issue_number = issue_url.group(1).split('/')[-1]
        else:
            print(
                f"ERROR: Could not capture the issue URL from the output:\n{output}", file=sys.stderr)
            exit(1)

        return cls(number=issue_number)

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
