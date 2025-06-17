import os
import subprocess
import sys
import re
import json
import asyncio


from classes.lazyload import Lazyload
from classes.gitter import Gitter
from classes.projectitem import Projectitem

class Project(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    type_to_switch_conversion = {
        'ProjectV2SingleSelectField': '--single-select-option-id',
        'ProjectV2Field': '--text'
    }

    # Instance methods

    def __init__(self, owner:str, number=str):
        super().__init__()

        self.set('workdir', os.getcwd())
        self.set('config_file', None)
        self.set('gh_validated', False)

        # Config - can be set in the .tt-config.json file in the repo root
        # Example:
        # {
        #     "project": {
        #         "owner": "thetechcollective",
        #         "number": "12"
        #     },
        #     "workon": {
        #         "status": "In Progress"
        #     },
        #     "deliver": {
        #         "status": "Delivery Initiated"
        #     }
        # }

        self.set('project_owner', owner)
        self.set('project_number', number)
        self.set('workon_field', 'Status')
        self.set('workon_field_value', 'In Progress')
        self.set('deliver_field', 'Status')
        self.set('deliver_field_value', 'Delivery Initiated')

        self.__read_config()

        if not self.get('project_owner') or not self.get('project_number'):
            print(
                f"Project owner or number not set - null values are currently not supported", file=sys.stderr)
            sys.exit(1)
        

    def get_item(self, url:str) -> Projectitem:
        """The project serves as a factory for project items.
        It will only return the project item if it is in the project's item-list.
        """
        self._load_initial()
        item = Projectitem()
        item.props = self.get('items')[url]

        has_start = False
        try:
            item.get('start')
            has_start = True
        except AssertionError:
            pass

            
        if not has_start:
            created_at = item.get_created_date()
            self.update_field(
                url=url,
                field='start',
                field_value=created_at
            )

        # Todo: update the field on the project.
        

        return item



    def _load_initial(self):
        try:
            #Using the project id from the properties as an indicator that the project has been loaded
            self.get('id')
            return
        except AssertionError:
            pass
        
        asyncio.run(self._load_manifest('init'))


        # load the json in self.get('project_raw_json') into a dict
        try:
            project_json = json.loads(self.get('raw_json_project'))
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Project JSON is not valid: {e}\n{self.get('raw_json_project')}")
            sys.exit(1)

        # iterate through the project_json and transfer each key-value pair to the properties
        for key, value in project_json.items():
            self.set(key, value)

        try:
            item_list_json = json.loads(self.get('raw_json_project_items'))
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Project item list JSON is not valid: {e}\n{self.get('raw_json_project_items')}")
            sys.exit(1)
        # item_list_json has one element 'items' which is a list of items
        # read throug each item and transfer it to self.props['items']
        # with the item['content']['url'] as the key and the value as the value
        for item in item_list_json['items']:
            if 'content' in item and 'url' in item['content']:
                item['project_id'] = self.get('id')
                self.props['items'][item['content']['url']] = item


        
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

        [id, result] = asyncio.run(Gitter(
            cmd=f"gh project view {number} --owner {owner} --format json --jq '.id'",
            msg="Get the project id").run(cache=True)
        )
        return id

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

    def update_field(self, owner=None, number=None, url=str, field=str, field_value=str, field_type=None):
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
                f"Field {field} in project {owner}/{number} doesn't have an id\n{e}")
            sys.exit(1)

        try:
            field_type = field_desc['type']
        except KeyError as e:
            raise KeyError(
                f"Field {field} in project {owner}/{number} doesn't have a type\n{e}")
            sys.exit(1)

        if field_type == "ProjectV2SingleSelectField":
            field_option_id = None
            for option in field_desc['options']:
                if option['name'] == field_value:
                    field_option_id = option['id']
                    break

            if field_option_id == None:
                raise KeyError(
                    f"Field option value {field_value} not found in field {field}")
                sys.exit(1)

            # convert the field type used internally in project definition to map the corresponting  switch used in the gh project edit-item cli
            try:
                type_switch = self.type_to_switch_conversion[field_type]
            except KeyError as e:
                raise KeyError(
                    f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n{e}")
                sys.exit(1)

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
                sys.exit(1)

        [output, result] = asyncio.run(Gitter(
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

        [id, result] = asyncio.run(Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project").run(cache=True)
        )
        return id

    def __read_config(self):
        """Read the configuration file and set the properties"""

        complete = False

        config = Config().config()

        try:
            project_owner = config["project"]["owner"]
            project_number = config["project"]["number"]
        except:
            print("⚠️ Could not find project owner or project number information in config.")
            project_owner = None
            project_number = None

        if project_owner is not None:
            self.set('project_owner', project_owner)

        if project_number is not None:
            self.set('project_number', project_number)
        
        # The configuration is complete if both project owner and number are set, the action triggers are optional since they have default values
        complete = True

        try:
            workon_action = config["workon"]["status"]
            deliver_action = config["deliver"]["status"]
        except:
            print("⚠️ Could not find workon status or deliver status information in config.")
            workon_action = None
            deliver_action = None

        if workon_action is not None:
            self.set('workon_action', workon_action)

        if deliver_action is not None:
            self.set('deliver_action', deliver_action)

        return complete
