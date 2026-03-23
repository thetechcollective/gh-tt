import asyncio
import json
import sys

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.label import Label
from gh_tt.classes.lazyload import Lazyload


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
        except ValueError:
            print(
                "ERROR: Could not parse the json", file=sys.stderr)
            sys.exit(1)

        # Iterate through issue_json and add each element to self.props
        for key, value in issue_json.items():
            issue.set(key, value)

        return issue

    def assign(self, assignee=str):
        """Assign the issue to a user"""

        issue_number = self.get('number')

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh issue edit {issue_number} --add-assignee '{assignee}'",
            msg="Assign @me to the issue").run()
        )

        self.set('assignee', assignee)
        return output
    
    def label(self, label:str):
        """Add a label to the issue"""

        existing_labels = self.get("labels")
        config = Config()._config_dict
        type_labels = [name for name, props in config["labels"].items() if props["category"] == "type"]

        for existing_label in existing_labels:
            if existing_label["name"] in type_labels:
                print(f"👌  Issue already has a \"{existing_label['name']}\" label.")
                return
        
        label = Label(name=label, create=True)
        issue_number = self.get('number')

        asyncio.run(Gitter(
            cmd=f"gh issue edit {issue_number} --add-label '{label.get('name')}'",
            msg=f"Add label '{label}' to the issue").run()
        )

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

        

