import asyncio
import json
import os
import re
import subprocess
import sys

from config import Config
from gitter import Gitter
from label import Label
from lazyload import Lazyload
from project import Project


class Issue(Lazyload):
    """Class used to represent a GitHub issue - in context of the current development branch"""

    def __init__(self):
        super().__init__()

    @classmethod
    def load(cls, number: int):
        issue = cls()

        issue.set('number', number)
        asyncio.run(issue._load_manifest('init'))

        try:
            issue_json = json.loads(issue.get('json'))
        except ValueError as e:
            pass
            print(
                f"ERROR: Could not parse the json", file=sys.stderr)
            sys.exit(1)

        # Iterate through issue_json and add each element to self.props
        for key, value in issue_json.items():
            issue.set(key, value)

        return issue

    @classmethod
    def create_new(cls, title=str, body=None, assign=None):
        """Create a new issue on the current repository
        Works as an alternative to the constructor, call it on the class and it will return a new Issue object

        Args:
            title (str): The title of the issue (required)
            body (str): The body of the issue  (defaults to None)
            assign: Assign to the issue (defaults to the current user)
        """

        issue = Issue()
        output = asyncio.run(issue._run('create_new_issue', {
            "title": title,
            "body": f"{body}" if body else "''",
            "assignee_switch": f"--assignee {assign}" if assign else ""
        }))

        # The output is a multitiline string like this:
        #
        #   Creating issue in lakruzz/gitsquash_lab
        #
        #   https://github.com/lakruzz/gitsquash_lab/issues/15

        # Capture the url of the issue and set it on the object
        # and capture the issue number from the tail of the url and set it on the object

        issue_url = re.search(r'(https://github.com/.*/issues/\d+)', output)
        if issue_url:
            issue_number = issue_url.group(1).split('/')[-1]
            print(f"{issue_url.group(1)}")
        else:
            print(
                f"ERROR: Could not capture the issue URL from the output:\n{output}", file=sys.stderr)
            exit(1)

        return cls().load(number=issue_number)

    def assign(self, assignee=str):
        """Assign the issue to a user"""

        issue_number = self.get('number')

        [output, result] = asyncio.run(Gitter(
            cmd=f"gh issue edit {issue_number} --add-assignee '{assignee}'",
            msg=f"Assign @me to the issue").run()
        )

        self.set('assignee', assignee)
        return output
    
    def label(self, label:str):
        """Add a label to the issue"""

        existing_labels = self.get("labels")
        config = Config()._config_dict
        type_labels = [name for name, props in config["labels"].items() if props["category"] == "type"]

        for l in existing_labels:
            if l["name"] in type_labels:
                print(f"⚠️  Issue already has a type label. The new label \"{label}\" will not be applied.")
                return
        
        label = Label(name=label, create=True)
        issue_number = self.get('number')

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh issue edit {issue_number} --add-label '{label.get('name')}'",
            msg=f"Add label '{label}' to the issue").run()
        )

        return output

    def comment(self, msg: str):
        """Add a comment to the issue"""

        issue_number = self.get('number')

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh issue comment {issue_number} --body '{msg}'",
            msg="Add a comment to the issue").run()
        )

        return output
    def reopen(self):
        """Reopen the issue"""

        asyncio.run(self._run('reopen'))
        return True

        

