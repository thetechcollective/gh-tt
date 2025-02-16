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
from devbranch import Devbranch

class Issue:
    """Class used to represent a GitHub issue - in context of the current development branch"""      
    
    props = {
        'number': None,
        'url': None,
        'title': None,
        'devbranch': None
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
    
    def __init__(self, devbranch=Devbranch, workdir=None, verbose=False):
        
        # Set the devbranch property
        self.set('devbranch', devbranch)
                     
        # Set the issue number from the branch name
        match = re.match(r'^(\d+).+', devbranch.props['branch_name'])
        if match:
            self.set('number', match.group(1))
        else:
            raise ValueError(f"Branch name {devbranch.props['branch_name']} does not contain an issue number")
            exit(1) 
            
        # Set the issue url
        number = self.get('number')
        url = None
        result = None
        gitter = Gitter(
            cmd=f"gh issue view {number} --json url --jq '.url'",
            workdir=devbranch.get('workdir'),
            verbose=devbranch.get('verbose'),
            die_on_error=True,
            msg="Get the url from the issue")
        [url, result] = gitter.run(cache=True)
        if result != None and result.returncode != 0:
            raise ValueError(f"Could not get the issue url on issue number: '{number}'\n{result.stderr}")
            exit(1) 
        self.set('url', url)
        
        # Set the issue title
        title = None
        result = None
        
        ## get the title of the issue
        [title, result] = Gitter(
            cmd=f"gh issue view {number} --json title --jq '.title'",
            workdir=devbranch.get('workdir'),
            verbose=devbranch.get('verbose'),
            die_on_error=False,
            msg=f"Get the title of the issue").run(cache=False)
        if result.returncode != 0:
            raise ValueError(f"Could not find title on issue number: '{number}'\n{result.stderr}")
            sys.exit(1)
        self.set('title', title)
        
                     

        
        
            
   