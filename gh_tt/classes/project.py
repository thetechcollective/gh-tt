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
        
        # Only set project-related actions if project integration is enabled
        # Check for both None and empty string values
        owner = self.get('project_owner')
        number = self.get('project_number')
        project_enabled = owner is not None and number is not None and owner and number
        self.set('project_enabled', project_enabled)
        
        if project_enabled:
            self.set('workon_action', config['workon']['status'])
            self.set('deliver_action', config['deliver']['status'])
        else:
            # Set default values when project integration is disabled
            self.set('workon_action', None)
            self.set('deliver_action', None)
    
    def is_project_enabled(self):
        """Check if project integration is enabled
        
        Returns:
            bool: True if project integration is enabled, False otherwise
        """
        return self.get('project_enabled')

    def get_project_id(self, owner=None, number=None):
        """Get the project id from the project owner and number

        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
        Returns:
            id (str): The project id
        Raises:
            RuntimeError: If the project owner or number is not set and project integration is disabled
        """
        if not self.is_project_enabled():
            print("⚠️  WARNING: Project integration is disabled. Cannot get project ID.", file=sys.stderr)
            return None
            
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            print("⚠️  WARNING: Project owner or number not configured. Cannot get project ID.", file=sys.stderr)
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
        Raises:
            RuntimeError: If the field is not found
        """
        if not self.is_project_enabled():
            print("⚠️  WARNING: Project integration is disabled. Cannot get field description.", file=sys.stderr)
            return {}

        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            print("⚠️  WARNING: Project owner or number not configured. Cannot get field description.", file=sys.stderr)
            return {}

        [field_json_str, result] = asyncio.run(Gitter(
            cmd=f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            msg="Get the field description in json format").run(cache=True)
        )

        field_json = json.loads(field_json_str)

        if field_json_str == '{}':
            print(f"⚠️  WARNING: Field {field} not found in project {owner}/{number}", file=sys.stderr)
            return {}
        return field_json

    def _validate_project_config(self, owner, number):
        """Validate project configuration
        
        Returns:
            tuple: (owner, number) if valid, (None, None) if invalid
        """
        if not self.is_project_enabled():
            print("⚠️  WARNING: Project integration is disabled.", file=sys.stderr)
            return None, None
            
        if not owner or not number:
            print("⚠️  WARNING: Project owner or number not configured.", file=sys.stderr)
            return None, None
            
        return owner, number

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

        owner, number = self._validate_project_config(owner, number)
        if not owner or not number:
            print("Skipping field update.", file=sys.stderr)
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

        return self._process_field_update(project_id, item_id, field_desc, field, field_value, owner, number)

    def _process_field_update(self, project_id, item_id, field_desc, field, field_value, owner, number):
        """Process the field update with the given parameters"""
        # read the field description
        try:
            field_id = field_desc['id']
        except KeyError:
            print(f"⚠️  WARNING: Field {field} in project {owner}/{number} doesn't have an id. Skipping field update.", file=sys.stderr)
            return None

        try:
            field_type = field_desc['type']
        except KeyError:
            print(f"⚠️  WARNING: Field {field} in project {owner}/{number} doesn't have a type. Skipping field update.", file=sys.stderr)
            return None
        
        value_switch = self._get_value_switch(field_type, field_desc, field_value, field)
        if not value_switch:
            return None

        [output, _] = asyncio.run(Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {value_switch}",
            msg="Update the field with the option").run()
        )
        return output

    def _get_value_switch(self, field_type, field_desc, field_value, field):
        """Get the appropriate value switch for the field type"""
        match field_type:
            case "ProjectV2SingleSelectField":
                field_option = next((option for option in field_desc['options'] if option['name'] == field_value), None)
                if field_option is None:
                    print(f"⚠️  WARNING: Field option value {field_value} not found in field {field}. Skipping field update.", file=sys.stderr)
                    return None

                # convert the field type used internally in project definition to map the corresponting switch used in the gh project edit-item cli
                try:
                    self.type_to_switch_conversion[field_type]
                except KeyError:
                    print(f"⚠️  WARNING: Field type {field_type} not supported. Skipping field update.", file=sys.stderr)
                    return None

                return f"--single-select-option-id {field_option['id']}"

            case "ProjectV2Field":
                if field_type == "ProjectV2Field":
                    return f"--date '{field_value}'" if re.match(r'\d{4}-\d{2}-\d{2}', field_value) else f"--text '{field_value}'"

            case _:
                print(f"⚠️  WARNING: Field type {field_type} not supported. Skipping field update.", file=sys.stderr)
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
        if not self.is_project_enabled():
            print("⚠️  WARNING: Project integration is disabled. Cannot add issue to project.", file=sys.stderr)
            return None
            
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')

        if not owner or not number:
            print("⚠️  WARNING: Project owner or number not configured. Cannot add issue to project.", file=sys.stderr)
            return None

        [item_id, _] = asyncio.run(Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project").run(cache=True)
        )
        return item_id
