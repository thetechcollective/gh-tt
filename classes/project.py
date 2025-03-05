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


class Project(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    type_to_switch_conversion = {
        'ProjectV2SingleSelectField': '--single-select-option-id',
        'ProjectV2Field': '--text'
    }

    # Instance methods

    def __init__(self, owner=None, number=None):
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
        
        self.__read_config() 
        
        if not self.get('project_owner') or not self.get('project_number'):
            print(f"Project owner or number not set - null values are currently not supported", file=sys.stderr)
            sys.exit(1)

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

        gitter = Gitter(
            cmd=f"gh project view {number} --owner {owner} --format json --jq '.id'",
            msg="Get the project id")
        [id, result] = gitter.run(cache=True)
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

        gitter = Gitter(
            cmd=f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            msg="Get the field description in json format")

        [field_json_str, result] = gitter.run(cache=True)
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
            
        if field_type ==  "ProjectV2SingleSelectField":
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
            if field_type ==  "ProjectV2Field":
                #if field values is a date in the format YYYY-MM-DD then --date else --text
                if re.match(r'\d{4}-\d{2}-\d{2}', field_value):
                    value_switch = f"--date '{field_value}'"
                else:
                    value_switch = f"--text '{field_value}'"
                
            else:
                raise KeyError(
                    f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n")
                sys.exit(1)


        gitter = Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {value_switch}",
            msg="Update the field with the option")

        # cache=False because this is a write operation
        [output, result] = gitter.run()
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

        gitter = Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            msg="Add the issue to the project")

        [id, result] = gitter.run(cache=True)
        return id

    def __read_config(self):
        """Read the configuration file and set the properties"""
        
        complete=False
        # Get the git root directory and set the config file
        [git_root, result] = Gitter(
            cmd="git rev-parse --show-toplevel",
            msg="Get the git root directory").run()
        if not git_root or result.returncode != 0:
            print(f"Could not determine the git root directory", file=sys.stderr)
            sys.exit(1)
        self.set('config_file', f"{git_root}/.gitconfig")


        # Check if the project owner can be read from .gitconfig
        [project_owner, result] = Gitter(
            cmd=f"git config --get -f {self.get('config_file')} project.owner",
            msg="Get the project owner from .gitconfig",
            die_on_error=False).run()
        # only override the default values if sucesfully read
        if not project_owner == '':
            self.set('project_owner', project_owner)

        # Check if the project number can be read from .gitconfig
        [project_number, result] = Gitter(
            cmd=f"git config --get -f {self.get('config_file')} project.number",
            msg="Get the project number from .gitconfig",
            die_on_error=False).run()
        # only override the default values if sucesfully read
        if not project_number == '':
            self.set('project_number', project_number)
            
        # The configuration is complete if both project owner and number are set, the action triggers are optional since they have default values
        complete=True          

        # Check if the workon action trigger can be read from .gitconfig
        [workon_action, result] = Gitter(
            cmd=f"git config --get -f {self.get('config_file')} project.workon",
            msg="Get the workon trigger action from .gitconfig",
            die_on_error=False).run()
        # split the workon action on : into field and value
        # only override the default values if both field and value are sucesfully read
        try:
            [workon_field, workon_field_value] = workon_action.split(':')
            if not workon_field == '' and not workon_field_value == '':
                self.set('workon_field', workon_field)
                self.set('workon_field_value', workon_field_value)            
        except ValueError as e:
            pass
           
        # Check if the workon action trigger can be read from .gitconfig                  
        [deliver_action, result] = Gitter(
            cmd=f"git config --get -f {self.get('config_file')} project.deliver",
            msg="Get the deliver trigger action from .gitconfig",
            die_on_error=False).run()
        # split the workon action on : into field and value
        # only override the default values if both field and value are sucesfully read
        try:
            [deliver_field, deliver_field_value] = deliver_action.split(':')
            if not deliver_field == '' and not deliver_field_value == '':
                self.set('deliver_field', deliver_field)
                self.set('deliver_field_value', deliver_field_value)
        except ValueError as e:
            pass
        
        return complete