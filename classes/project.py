import os
import subprocess
import sys
import re

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

from runner import run

class Project:
    """Class used to represent the Devbranch for a development contribution"""

    props = {
        'project_owner': 'lakruzz',
        'project_number': '12',
        'project_id': None,
        'item_id': None,
        'field_id': None,
        'field_type': None,
        'option_id': None,
        'issue_url': None,
        'verbose': False,
        'workdir': None,
    }

    props['workdir'] = os.getcwd()

  
    def verbose(self, verbose):
        self.props['verbose'] = verbose
        
    def verbose_print(self, message):
        if self.props['verbose'] == True:
            print(message)
            

    # Instance methods
    
    def __init__(self, owner=str, number=int, workdir=None, verbose=False):
        self.props['verbose'] = verbose
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.props['workdir'] = os.path.abspath(workdir)
        self.__read_project()
            
    def __read_project(self):
        """Desinged to be called from __init__ to read the project context in the repo"""
        ## get the project id
        [self.props['project_id'], result] = run(
            f"gh project view --owner {self.props['project_owner']} {self.props['project_number']} --format json --jq '.id'",
            msg="Get the project id")


