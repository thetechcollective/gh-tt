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
        'workdir': None,
        'project_id': None,
        'item_id': None,
        'field_id': None,
        'field_type': None,
        'option_id': None,
        'issue_url': None
    }

    props['workdir'] = os.getcwd()

  
    def verbose(self, verbose):
        self.props['verbose'] = verbose
        
    def set(self, key, value):
        self.props[key] = value
        return self.props[key]
    
    def get(self, key):
        if key not in self.props:
            raise KeyError(f"Key {key} not found in properties")
            sys.exit(1)
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
        
        
    def get_item_id_from_url(self, owner=None, number=None, url=str):
        """Get the project item id from the issue url (consider using add_issue(url) to get the item-id instead)
        
        Args:
            owner (str): The owner of the project (optional)
            number (int): The project number (optional)
            url (str): The url of the issue
        Returns:
            item_id (str): The item id of the issue if it is added to the project
            None: If the issue is not added to the project
        Raises:
            RuntimeError: If the issue is not found in the project
        """
        
        # User overriden values is applicable, else use the class cached values
        if not owner:
            owner = self.get('project_owner')
        if not number:
            number = self.get('project_number')
            
        [item_id, result] = run(
            f"gh project item-list {number} --owner {owner} --limit 1000 --format json --jq '.items[] | select(.content.url == \"{url}\") | .id'",
            verbose=self.props['verbose'],
            msg="Get the item id from the url")
        if item_id == '':
            raise RuntimeError(f"Item with url {url} not found in project {owner}/{number}")
            sys.exit(1)
        return item_id
    
    def get_url_from_issue(self, issue=int):
        """Get the url of the issue in context of the current repository
        
        Args:
            issue (int): The issue number
        Returns: 
            url (str): The url of the issue
        Raises:
            RuntimeError: If the issue number is not found
        """
        [url, result] = run(
            f"gh issue view {issue} --json url --jq '.url'",
            verbose=self.props['verbose'],
            msg="Get the url from the issue")
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
            owner = self.props['project_owner']
        if not number:
            number = self.props['project_number']
            
        [id, result] = run(
            f"gh project view {number} --owner {owner} --format json --jq '.id'",
            verbose=self.props['verbose'],
            msg="Get the project id")      
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
            owner = self.props['project_owner']
        if not number:
            number = self.props['project_number']
                    
        [field_json_str, result] = run(
            f"gh project field-list {number} --owner {owner} --format json --jq '.fields[] | select(.name == \"{field}\")'",
            verbose=self.props['verbose'],
            msg="Get the field description in json format")
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
            owner = self.props['project_owner']
        if not number:
            number = self.props['project_number']

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
          
        type_to_switch_conversion = {
            'ProjectV2SingleSelectField': '--single-select-option-id',
            'ProjectV2Field': '--text'
            }
                     
        type_switch = type_to_switch_conversion[field_type]     
        if type_switch == None:
            raise RuntimeError(f"Field type {field_type} not supported")
            sys.exit(1)
             
        [output, result] = run(
            f"gh project item-edit --project-id {project_id} --field-id {field_id} --id {item_id} {type_switch} {field_option_id}",
            verbose=self.props['verbose'],
            msg="Update the field with the option")    
        
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
            owner = self.props['project_owner']
        if not number:
            number = self.props['project_number']
            
        gitter = Gitter(
            cmd=f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
            verbose=self.props['verbose'],
            msg="Add the issue to the project")
        
        [id, result] = gitter.run(cache=True)
        return id
        
            
    #    [id, result] = run(
    #        f"gh project item-add {number} --owner {owner} --url {url} --format json --jq '.id'",
    #        verbose=self.props['verbose'],
    #        msg="Add the issue to the project")
    #    return id
         
            
            


