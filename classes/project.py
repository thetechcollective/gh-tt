import os
import subprocess
import sys
import re
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

from runner import run
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
    
    def __init__(self, owner=str, number=int, workdir=None, verbose=False):
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.set('workdir', os.path.abspath(workdir))
            
        self.set('project_owner', owner)
        self.set('project_number', number)
        self.set('verbose', verbose)
        
        
    def get_url_from_issue(self, issue=int):
        """Get the url of the issue in context of the current repository
        
        Args:
            issue (int): The issue number
        Returns: 
            url (str): The url of the issue
        Raises:
            RuntimeError: If the issue number is not found
        """
        gitter = Gitter(
            cmd=f"gh issue view {issue} --json url --jq '.url'",
            verbose=self.get('verbose'),
            msg="Get the url from the issue")
        [url, result] = gitter.run(cache=True)
        return url
    
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
        
        if field_json_str == '':
            raise RuntimeError(f"Field {field} not found in project {owner}/{number}\n{result.stderr}")
            sys.exit(1)
        return field_json
    
    def update_field(self, owner=str, number=int, url=str, field=str, field_value=str):
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
        field_id = field_desc['id']
        field_type= field_desc['type']
        field_option_id = None
        for option in field_desc['options']:
            if option['name'] == field_value:
                field_option_id = option['id']  
                
        if field_id == None or field_option_id == None:
            raise RuntimeError(f"Field {field} not found in project {owner}/{number}")
            sys.exit(1)
        
        if field_option_id == None:
            raise RuntimeError(f"Field option value {field_value} not found in field {field}")
            sys.exit(1)
        
        # convert the field type used internally in project definition to map the corresponting  switch used in the gh project edit-item cli  
        type_switch = self.type_to_switch_conversion[field_type]  
        if type_switch == None:
            raise RuntimeError(f"Field type {field_type} not supported. It may be that the field type is just not supported in this extension yet. - Please open an issue or discussion on the repository")
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
         
            
            


