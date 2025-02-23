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
        self.set('project_owner', None)
        self.set('project_number', None)
        self.set('gh_validated', False)
        self.set('workon_field', None)
        self.set('workon_field_value', None)
        self.set('deliver_field', None)
        self.set('deliver_field_value', None)

        if owner == None or number == None:  # TODO should always read the config file!
            [git_root, result] = Gitter(
                cmd="git rev-parse --show-toplevel",
                msg="Get the git root directory").run()

            if not git_root or result.returncode != 0:
                raise FileNotFoundError(  # TODO should not raise an error, just exit
                    f"Could not determine the git root directory")
            self.set('config_file', f"{git_root}/.gitconfig")

            [self.props['project_owner'], result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.owner",
                msg="Get the project owner from .gitconfig").run()
            if self.get('project_owner') == '':
                # TODO should not raise an error, just exit
                raise ValueError("Project owner not found in the git config")

            [self.props['project_number'], result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.number",
                msg="Get the project number from .gitconfig").run()
            if self.get('project_number') == '':
                raise ValueError("Project number not found in the git config")
                sys.exit(1)

            [workon_action, result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.workon",
                msg="Get the workon trigger action from .gitconfig").run()

            # split the workon action on : into field and value
            try:
                [self.props['workon_field'], self.props['workon_field_value']  # TODO use the set method
                 ] = workon_action.split(':')
            except ValueError as e:
                raise ValueError(  # TODO should not raise an error, just exit
                    "Failed to read workon_field and workon_field_value from the .gitconfig")
                sys.exit(1)

            [workon_action, result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.deliver",
                # TODO should not raise an error, just exit
                msg="Get the deliver trigger action from .gitconfig").run()

            # split the workon action on : into field and value
            try:
                [self.props['deliver_field'], self.props['deliver_field_value']  # TODO use the set method
                 ] = workon_action.split(':')
            except ValueError as e:
                raise ValueError(  # TODO should not raise an error, just exit
                    "Failed to read deliver_field and deliver_field_value from the .gitconfig")
                sys.exit(1)

        else:
            self.set('project_owner', owner)
            self.set('project_number', number)

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
