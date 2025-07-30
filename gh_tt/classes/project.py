import asyncio
import json
import re
import sys
from pathlib import Path
from types import MappingProxyType

from gh_tt.classes.config import Config
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.lazyload import Lazyload


class Project(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    type_to_switch_conversion = MappingProxyType({
        'ProjectV2SingleSelectField': '--single-select-option-id',
        'ProjectV2Field': '--text'
    })

    # Instance methods

    def __init__(self):
        super().__init__()

        self.set('workdir', Path.cwd())
        self.set('config_file', None)
        self.set('gh_validated', value=False)

        config = Config().config()

        self.set('project_owner', config['project']['owner'])
        self.set('project_number', config['project']['number'])
        self.set('workon_action', config['workon']['status'])
        self.set('deliver_action', config['deliver']['status'])

    def get_project_id(self, owner=None, number=None):
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

        [project_id, _] = asyncio.run(Gitter(
            cmd=f"gh project view {number} --owner {owner} --format json --jq '.id'",
            msg="Get the project id").run(cache=True)
        )
        return project_id

    def get_field_description(self, owner=None, number=None, field=str):
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

        [field_json_str, result] = asyncio.run(Gitter(
            cmd=f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            msg="Get the field description in json format").run(cache=True)
        )

        field_json = json.loads(field_json_str)

        if field_json_str == '{}':
            raise KeyError(  # TODO should not raise an error, just exit
                f"Field {field} not found in project {owner}/{number}\n{result.stderr}")
            sys.exit(1)
        return field_json

    def update_field(self, url: str, field: str, field_value: str, owner: str | None = None, number: int | None = None, field_type=None):
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

        project_id = self.get_project_id()
        item_id = self.add_issue(url=url)
        field_desc = self.get_field_description(field=field)

        # read the field description
        try:
            field_id = field_desc['id']
        except KeyError as e:
            raise KeyError(
                f"Field {field} in project {owner}/{number} doesn't have an id\n{e}") from e

        try:
            field_type = field_desc['type']
        except KeyError as e:
            raise KeyError(
                f"Field {field} in project {owner}/{number} doesn't have a type\n{e}") from e
        
        match field_type:
            case "ProjectV2SingleSelectField":
                field_option = next((option for option in field_desc['options'] if option['name'] == field_value), None)
                if field_option is None:
                    raise KeyError(
                        f"Field option value {field_value} not found in field {field}")

                # convert the field type used internally in project definition to map the corresponting switch used in the gh project edit-item cli
                try:
                    self.type_to_switch_conversion[field_type]
                except KeyError as e:
                    raise KeyError(
                        f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n{e}") from e

                value_switch = f"--single-select-option-id {field_option['id']}"

            case "ProjectV2Field":
                if field_type == "ProjectV2Field":
                    value_switch = f"--date '{field_value}'" if re.match(r'\d{4}-\d{2}-\d{2}', field_value) else f"--text '{field_value}'"

            case _:
                raise KeyError(
                    f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n")

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {value_switch}",
            msg="Update the field with the option").run()
        )
        return output

    def add_issue(self, owner=None, number=None, url=str):
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

        [item_id, _] = asyncio.run(Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project").run(cache=True)
        )
        return item_id
