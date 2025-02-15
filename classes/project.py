import os
import subprocess
import sys
import re
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

from gitter import Gitter

class Project:
    """Class used to represent the Devbranch for a development contribution"""
    
    props = {
        'project_owner': 'None',
        'project_number': 'None',
        'verbose': False,
        'workdir': os.getcwd()
    }
    
    type_to_switch_conversion = {
        'ProjectV2SingleSelectField': '--single-select-option-id',
        'ProjectV2Field': '--text'
        }
        
    def set(self, key, value):
        """Some syntactic sugar to set the class properties
        
        Args:
            key (str): The key to set in the class properties
            value: The value to set the key to
        """
        
        self.props[key] = value
        return self.props[key]
    
    def get(self, key):
        """Some syntactic sugar to get the class properties
        
        Args:
            key (str): The key to get from the class properties - The key must exist in the class properties

        Returns:
            value: The value of the key in the class properties
        """    
        assert key in self.props, f"Property {key} not found on class"
        return self.props[key]

    # Instance methods
    
    def __init__(self, owner=None, number=None, workdir=None, verbose=False):
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.set('workdir', os.path.abspath(workdir))

        self.set('verbose', verbose)
            
        if owner == None or number == None:
            result = subprocess.run("git rev-parse --show-toplevel", capture_output=True, text=True, shell=True)
            git_root = result.stdout.strip()
            if not git_root or result.returncode != 0:
                raise RuntimeError(f"Could not determine the git root directory")
            self.set('config_file', f"{git_root}/.gitconfig")
            
            [self.props['project_owner'], result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.owner",
                verbose=self.get('verbose'),
                msg="Get the project owner from .gitconfig").run(cache=True)
            if self.get('project_owner') == '':
                raise ValueError("Project owner not found in the git config")
            
            [self.props['project_number'], result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.number",
                verbose=self.get('verbose'),
                msg="Get the project number from .gitconfig").run(cache=True)
            if self.get('project_number') == '':
                raise ValueError("Project number not found in the git config")
                sys.exit(1)
            
            [workon_action, result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.workon",
                verbose=self.get('verbose'),
                msg="Get the workon trigger action from .gitconfig").run(cache=True)
            
            # split the workon action on : into field and value
            try:
                [self.props['workon_field'], self.props['workon_field_value']] = workon_action.split(':')
            except ValueError as e:
                raise ValueError("Failed to read workon_field and workon_field_value from the .gitconfig")
                sys.exit(1)

            [workon_action, result] = Gitter(
                cmd=f"git config get -f {self.get('config_file')} project.deliver",
                verbose=self.get('verbose'),
                msg="Get the deliver trigger action from .gitconfig").run(cache=True)
            
            # split the workon action on : into field and value
            try:
                [self.props['deliver_field'], self.props['deliver_field_value']] = workon_action.split(':')
            except ValueError as e:
                raise ValueError("Failed to read deliver_field and deliver_field_value from the .gitconfig")
                sys.exit(1)       
              
        else:
            self.set('project_owner', owner)
            self.set('project_number', number)   
        
        [self.props['gh_validated'],msg] = self.validate_gh_access()
        if not self.get('gh_validated'):
            print (f"WARNING\nYour GH CLI is not setup correctly:{msg}", file=sys.stderr)
        
    def validate_gh_access(self):
        """Check if the user has sufficient access to the github cli
        
        Returns:
            [result (bool), status (str)] : True/'' if the validation is OK, False/Error message if the validation fails
        """
        gitter = Gitter(
            cmd="gh --version",
            verbose=self.get('verbose'),
            msg="Check if the user has access to right version of gh CLI")
        [stdout, result] = gitter.run(cache=False)
        
        # Validate that the version is => 2.55.0
        # The command returns something like this:
        #    gh version 2.65.0 (2025-01-06)
        #    https://github.com/cli/cli/releases/tag/v2.65.0
        
        version = stdout.split()[2]
        if version < '2.55.0':
            return [False, f"gh version {version} is not supported. Please upgrade to version 2.55.0 or higher"]
        
        [stdout, result] = Gitter(
            cmd="gh auth status",
            verbose=self.get('verbose'),
            msg="Check if the user has sufficient access to update projects").run(cache=False)
        
        # Valiadate that we have reaacce to projects
        # The command returns something like this:
        #  github.com
        #    ✓ Logged in to github.com account lakruzz (/home/vscode/.config/gh/hosts.yml)
        #    - Active account: true
        #    - Git operations protocol: https
        #    - Token: gho_************************************
        #    - Token scopes: 'gist', 'read:org', 'read:project', 'repo', 'workflow'
        # The token scopes must contain 'read:project'
        if "'project'" not in stdout:
            return [False, f"gh token does not have the required scope 'project'"]
        
        return [True, '']
            
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
            verbose=self.get('verbose'),
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
            verbose=self.props['verbose'],
            msg="Get the field description in json format")
        
        [field_json_str, result] = gitter.run(cache=True)
        field_json = json.loads(field_json_str)
        
        if field_json_str == '{}':
            raise KeyError(f"Field {field} not found in project {owner}/{number}\n{result.stderr}")
            sys.exit(1)
        return field_json
    
    def update_field(self, owner=None, number=None, url=str, field=str, field_value=str):
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
            raise KeyError(f"Field {field} in project {owner}/{number} doesn't have an id\n{e}")
            sys.exit(1)     

        try:
            field_type= field_desc['type']
        except KeyError as e:
            raise KeyError(f"Field {field} in project {owner}/{number} doesn't have a type\n{e}")
            sys.exit(1)

        field_option_id = None
        for option in field_desc['options']:
            if option['name'] == field_value:
                field_option_id = option['id']  
                break
        
        if field_option_id == None:
            raise KeyError(f"Field option value {field_value} not found in field {field}")
            sys.exit(1)
        
        # convert the field type used internally in project definition to map the corresponting  switch used in the gh project edit-item cli  
        try:
            type_switch = self.type_to_switch_conversion[field_type]
        except KeyError as e:
            raise KeyError(f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository\n{e}")
            sys.exit(1)
             
        gitter = Gitter(
            cmd=f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {type_switch} {field_option_id}",
            verbose=self.get('verbose'),
            msg="Update the field with the option") 
        
        [output, result] = gitter.run(cache=False)   # cache=False because this is a write operation 
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
            verbose=self.props['verbose'],
            msg="Add the issue to the project")
        
        [id, result] = gitter.run(cache=True)
        return id