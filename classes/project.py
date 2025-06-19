from lazyload import Lazyload
from gitter import Gitter
import os
import subprocess
import sys
import re
import json
import asyncio

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Project(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    type_to_switch_conversion = {
        'ProjectV2SingleSelectField': '--single-select-option-id',
        'ProjectV2Field': '--text'
    }

    # Instance methods

    async def __init__(self, owner=None, number=None):
        super().__init__()

        self.set('workdir', os.getcwd())
        self.set('config_file', None)
        self.set('gh_validated', False)

        # Config - can be set in the .gitconfig file in the repo root
        # Example:
        # [project]
        #   owner = thetechcollective
        #   number = 12
        #   workon = Status:In Progress
        #   deliver = Status:Delivery Initiated

        self.set('project_owner', owner)
        self.set('project_number', number)
        self.set('workon_field', 'Status')
        self.set('workon_field_value', 'In Progress')
        self.set('deliver_field', 'Status')
        self.set('deliver_field_value', 'Delivery Initiated')

        await self.__read_config()

        if not self.get('project_owner') or not self.get('project_number'):
            print(
                f"Project owner or number not set - null values are currently not supported", file=sys.stderr)
            sys.exit(1)

    async def get_project_id(self, owner=None, number=None):
        """Get the project id from the project owner and number

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
        Returns:
            id (str): The project id
        Raises:
            RuntimeError: If the project owner or number is not
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        [id, _] = await Gitter(
            cmd=f"gh project view {number} --owner {owner} --format json --jq '.id'",
            msg="Get the project id").run(cache=True)

        return id

    async def get_field_description(self, field: str, owner=None, number=None):
        """Get the field descriptions from the project

        Args:   
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            field (str): The field name 
        Returns:
            field_json (dict): The field description in json format
        Raises:
            RuntimeError: If the field is not found
        """

        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        [field_json_str, result] = await Gitter(
            cmd=f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            msg="Get the field description in json format").run(cache=True)

        field_json = json.loads(field_json_str)

        if field_json_str == '{}':
            raise KeyError(  # TODO should not raise an error, just exit
                f"Field {field} not found in project {owner}/{number}\n{result.stderr}")
        
        return field_json

    async def update_field(self, owner=None, number=None, url=str, field=str, field_value=str, field_type=None):
        """Update the field with the value

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            url (str): The url of the issue
            field (str): The field name
            field_value (str): The field value
        Returns:
            result (str): The result of the update
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        project_id, item_id, field_desc = await asyncio.gather(
            self.get_project_id(),
            self.add_issue(url=url),
            self.get_field_description(field=field)
        )

        # read the field description
        try:
            field_id = field_desc['id']
        except KeyError as e:
            raise KeyError(
                f"Field {field} in project {owner}/{number} doesn't have an id\n{e}")

        try:
            field_type = field_desc['type']
        except KeyError as e:
            raise KeyError(
                f"Field {field} in project {owner}/{number} doesn't have a type\n{e}")

        if field_type == "ProjectV2SingleSelectField":
            field_option_id = None
            for option in field_desc['options']:
                if option['name'] == field_value:
                    field_option_id = option['id']
                    break

            if field_option_id == None:
                raise KeyError(
                    f"Field option value {field_value} not found in field {field}")

            # convert the field type used internally in project definition to map the corresponting  switch used in the gh project edit-item cli
            try:
                self.type_to_switch_conversion[field_type]
            except KeyError as e:
                raise KeyError(
                    f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n{e}")

            value_switch = f"--single-select-option-id {field_option_id}"

        else:
            if field_type == "ProjectV2Field":
                # if field values is a date in the format YYYY-MM-DD then --date else --text
                if re.match(r'\d{4}-\d{2}-\d{2}', field_value):
                    value_switch = f"--date '{field_value}'"
                else:
                    value_switch = f"--text '{field_value}'"

            else:
                raise KeyError(
                    f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n")

        [output, _] = await Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {value_switch}",
            msg="Update the field with the option").run()

        return output

    async def add_issue(self, owner=None, number=None, url=str):
        """Add an issue to the project. This function is idempotent, It doesn't affect the
        project if the issue is already added to the project.

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            url (str): The url of the issue
        Returns:
            result (str): item-id of the issue in the project
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        [id, _] = await Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project").run(cache=True)

        return id

    async def __read_config(self):
        """Read the configuration file and set the properties"""

        complete = False
        # Get the git root directory and set the config file
        git_root = Gitter.git_root
        self.set('config_file', f"{git_root}/.gitconfig")

        # TODO: move this into props.json!
        tasks = [
            # Check if project owner can be read from .gitconfig
            Gitter(
                cmd=f"git config --get -f {self.get('config_file')} project.owner",
                msg="Get the project owner from .gitconfig",
                die_on_error=False
            ).run(),
            # Check if the project number can be read from .gitconfig
            Gitter(
                cmd=f"git config --get -f {self.get('config_file')} project.number",
                msg="Get the project number from .gitconfig",
                die_on_error=False
            ).run(),
             # Check if the project action for workon can be read from .gitconfig
            Gitter(
                cmd=f"git config --get -f {self.get('config_file')} project.workon",
                msg="Get the workon trigger action from .gitconfig",
                die_on_error=False
            ).run(),
            # Check if the project action for deliver can be read from .gitconfig
            Gitter(
                cmd=f"git config --get -f {self.get('config_file')} project.deliver",
                msg="Get the deliver trigger action from .gitconfig",
                die_on_error=False
            ).run()
        ]

        results = await asyncio.gather(*tasks)

        project_owner, _ = results[0]
        project_number, _ = results[1]
        workon_action, _ = results[2]
        deliver_action, _ = results[3] 

        # only override the default values if successfully read
        if not project_owner == '':
            self.set('project_owner', project_owner)

        # only override the default values if successfully read
        if not project_number == '':
            self.set('project_number', project_number)

        # The configuration is complete if both project owner and number are set, the action triggers are optional since they have default values
        complete = True

        # split the workon action on : into field and value
        # only override the default values if both field and value are successfully read
        try:
            [workon_field, workon_field_value] = workon_action.split(':')
            if not workon_field == '' and not workon_field_value == '':
                self.set('workon_field', workon_field)
                self.set('workon_field_value', workon_field_value)
        except ValueError as e:
            pass

        # split the workon action on : into field and value
        # only override the default values if both field and value are successfully read
        try:
            [deliver_field, deliver_field_value] = deliver_action.split(':')
            if not deliver_field == '' and not deliver_field_value == '':
                self.set('deliver_field', deliver_field)
                self.set('deliver_field_value', deliver_field_value)
        except ValueError as e:
            pass

        return complete
