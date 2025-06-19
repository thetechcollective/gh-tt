from config import Config
from project import Project
from lazyload import Lazyload
from gitter import Gitter
from label import Label
import os
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

        self._load_manifest('init')

        try:
            issue_json = json.loads(self.get('json'))
        except ValueError as e:
            pass
            print(
                f"ERROR: Could not parse the json", file=sys.stderr)
            sys.exit(1)

        # Iterate through issue_json and add each element to self.props
        for key, value in issue_json.items():
            self.set(key, value)

    @classmethod
    async def create_new(cls, title=str, body=None, assign=None):
        """Create a new issue on the current repository
        Works as an alternative to the constructor, call it on the class and it will return a new Issue object

        Args:
            title (str): The title of the issue (required)
            body (str): The body of the issue  (defaults to None)
            assign: Assign to the issue (defaults to the current user)
        """

        body_switch = f"--body '{body}'" if body is not None else "--body ''"
        assign_switch = f"--assignee '{assign}'" if assign is not None else ""

        [output, _] = await Gitter(
            cmd=f"gh issue create --title '{title}' {body_switch} {assign_switch}",
            msg="Create a new issue").run()

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
            print(f"{issue_url.group(1)}")
        else:
            print(
                f"ERROR: Could not capture the issue URL from the output:\n{output}", file=sys.stderr)
            sys.exit(1)

        return cls(number=issue_number)

    async def add_to_project(self, owner: str, number: int):
        """Add the issue to a project column"""

        if self.get('item_id') is not None:
            return self.get('item_id')

        url = self.get('url')
        gitter = Gitter(
            cmd=f"gh project item-add {number}  --owner {owner} --url {url} --format json --jq '.id'",
            die_on_error=False,
            msg="Add the issue to a project column")
        [item_id, result] = await gitter.run()

        if result.returncode != 0:
            print(
                f"ERROR: Could not add the issue to the project {owner}/{number}\n{result.stderr}", file=sys.stderr)
            exit(1)

        self.set('item_id', item_id)

        return item_id

    async def assign(self, assignee: str):
        """Assign the issue to a user"""

        issue_number = self.get('number')

        [output, _] = await Gitter(
            cmd=f"gh issue edit {issue_number} --add-assignee '{assignee}'",
            msg=f"Assign @me to the issue").run()

        self.set('assignee', assignee)
        return output
    
    async def label(self, label:str):
        """Add a label to the issue"""

        existing_labels = self.get("labels")
        config = Config().config()
        type_labels = [name for name, props in config["labels"].items() if props["category"] == "type"]

        for l in existing_labels:
            if l["name"] in type_labels:
                print(f"⚠️  Issue already has a type label. The new label \"{label}\" will not be applied.")
                return
        
        label = await Label(name=label, create=True)
        issue_number = self.get('number')

        [output, _] = await Gitter(
            cmd=f"gh issue edit {issue_number} --add-label '{label.get('name')}'",
            msg=f"Add label '{label}' to the issue").run()

        return output

    async def comment(self, msg: str):
        """Add a comment to the issue"""

        issue_number = self.get('number')

        [output, _] = await Gitter(
            cmd=f"gh issue comment {issue_number} --body '{msg}'",
            msg="Add a comment to the issue").run()

        return output
    
    async def reopen(self):
        """Reopen the issue"""

        await self._run('reopen')
        return True

        

