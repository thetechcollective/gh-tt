import os
import subprocess
import sys
import re

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Devbranch:
    """Class used to represent the Devbranch for a development contribution"""

    # Class variables

    issue_number = None 
    branch_name = None
    pull_request = None
    workdir = os.getcwd() # Required, therefore also  set at class level to allow a null constructor
    git_root = None

    def __run_git(self, cmd=str):
        result = subprocess.run(
        cmd, capture_output=True, text=True, shell=True, cwd=self.workdir)
        return result    
          
    # Instance methods
    def __init__(self, workdir=None):
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
            self.workdir = os.path.abspath(workdir)

        result = self.__run_git('git rev-parse --show-toplevel')
        if not result.returncode == 0: 
            raise FileNotFoundError(f"{result.stderr}")
            sys.exit(1)
        self.git_root = result.stdout.strip()

        self.__read_context()

    def __read_context(self):
        """Desinged to be called from __init__ to read the branch context in the repo"""
        
        result = self.__run_git('git rev-parse --abbrev-ref HEAD')
        if not result.returncode == 0:
            raise FileNotFoundError(f"{result.stderr}")
            sys.exit(1)
        self.branch_name = result.stdout.strip()
 
         # Check if the branch name is in the format issue-<number>
        match = re.match(r'^(\d+).+', self.branch_name)
        if match:
            self.issue_number = match.group(1)
        else:
            self.issue_number = None
        
        
        
        
        
        



    


