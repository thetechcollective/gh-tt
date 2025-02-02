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

    props = {
        'issue_number': None,
        'branch_name': None,
        'pull_request': None,
        'commit_message': None,
        'SHA1': None,
        'new_message': None,
        'git_root': None,
        'workdir': None,
        'default_branch': 'main'
    }
    
    props('workdir') = os.getcwd()


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
            self.props('workdir') = os.path.abspath(workdir)

        result = self.__run_git('git rev-parse --show-toplevel')
        if not result.returncode == 0: 
            raise FileNotFoundError(f"{result.stderr}")
            sys.exit(1)
        self.props('git_root') = result.stdout.strip()

        self.__read_context()

    def __read_context(self):
        """Desinged to be called from __init__ to read the branch context in the repo"""
        
        # Get the current branch name
        result = self.__run_git('git rev-parse --abbrev-ref HEAD')
        if not result.returncode == 0:
            raise FileNotFoundError(f"{result.stderr}")
            sys.exit(1)
        self.props(branch_name) = result.stdout.strip()
        
        # Get the SHA1 of the current branch
        result = self.__run_git('git rev-parse HEAD')
        if not result.returncode == 0:
            raise FileNotFoundError(f"{result.stderr}")
            sys.exit(1) 
        self.props('SHA1') = result.stdout.strip()
 
         # Get the issue number
        match = re.match(r'^(\d+).+', self.branch_name)
        if match:
            self.props('issue_number') = match.group(1)
        else:
            self.props('issue_number') = None
            
        # get the most recent commit message
            self.props('commit_message') = self.__run_git('git show -s --format=%B {self.branch_name}')
            
            
        # If self.issue_number is not None, then check if the commit message contains 
        # fixed #<issue_number> or closes #<issue_number> and if not, add it
        if self.issue_number:
            if not re.search(r'fixed #'+self.props('issue_number'), self.props('commit_message')) and not re.search(r'closes #'+self.props('issue_number'), self.props('commit_message')):
                self.props('new_message') = self.props('commit_message') + f" - closed #{self.issue_number}"
            else:
                self.props('new_message') = self.props('commit_message')
        else:
            self.props('new_message') = self.props('commit_message')
        
        
            
            
    def __collapse(self):
        """Collapse the current branch into a single commit"""
        self.props('merge_base') = self.__run_git('git merge-base {self.branch_name} {self.default_branch}')
         
        cmd=f"git commit-tree {self.props('branch_name')}^{{tree}} -p {self.props('merge_base')} -m {self.props('new_message')}"        
    
        # print self.props to stdout
        print(self.props)
        print (cmd)
        
        
        
        
        
        



    


