import asyncio
import json
import re
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
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            return None

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
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            return {}

        [field_json_str, result] = asyncio.run(Gitter(
            cmd=f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            msg="Get the field description in json format").run(cache=True)
        )

        field_json = json.loads(field_json_str)

        if field_json_str == '{}':
            return {}
        return field_json

    def update_field(self, url: str, field: str, field_value: str, owner: str | None = None, number: int | None = None):
        """Update the field with the value

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            url (str): The url of the issue
            field (str): The field name
            field_value (str): The field value
        Returns:
            result (str): The result of the update, or None if project integration is disabled
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            return None

        project_id = self.get_project_id()
        if not project_id:
            return None
            
        item_id = self.add_issue(url=url)
        if not item_id:
            return None
            
        field_desc = self.get_field_description(field=field)
        if not field_desc:
            return None

        return self._process_field_update(project_id, item_id, field_desc, field_value)

    def _process_field_update(self, project_id, item_id, field_desc, field_value):
        """Process the field update with the given parameters"""
        # read the field description
        try:
            field_id = field_desc['id']
        except KeyError:
            return None

        try:
            field_type = field_desc['type']
        except KeyError:
            return None
        
        value_switch = self._get_value_switch(field_type, field_desc, field_value)
        if not value_switch:
            return None

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {value_switch}",
            msg="Update the field with the option").run()
        )
        return output

    def _get_value_switch(self, field_type, field_desc, field_value):
        """Get the appropriate value switch for the field type"""
        match field_type:
            case "ProjectV2SingleSelectField":
                field_option = next((option for option in field_desc['options'] if option['name'] == field_value), None)
                if field_option is None:
                    return None

                # convert the field type used internally in project definition to map the corresponting switch used in the gh project edit-item cli
                try:
                    self.type_to_switch_conversion[field_type]
                except KeyError:
                    return None

                return f"--single-select-option-id {field_option['id']}"

            case "ProjectV2Field":
                if field_type == "ProjectV2Field":
                    return f"--date '{field_value}'" if re.match(r'\d{4}-\d{2}-\d{2}', field_value) else f"--text '{field_value}'"

            case _:
                return None
        return None

    def add_issue(self, owner=None, number=None, url=str):
        """Add an issue to the project. This function is idempotent, It doesn't affect the
        project if the issue is already added to the project.

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            url (str): The url of the issue
        Returns:
            result (str): item-id of the issue in the project, or None if project integration is disabled
        """
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            return None

        [item_id, _] = asyncio.run(Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project").run(cache=True)
        )
        return item_id
