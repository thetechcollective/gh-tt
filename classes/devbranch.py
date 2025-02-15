import os
import subprocess
import sys
import re

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

#from runner import run
from project import Project
from gitter import Gitter

class Devbranch:
    """Class used to represent the Devbranch for a development contribution"""

    props = {
        'workdir': os.getcwd()}
        
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
    def __init__(self, workdir=None, verbose=False):
        
        self.set('verbose', verbose)
               
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.set('workdir', os.path.abspath(workdir))
            
        # Git fetch    
        [output, result] = Gitter(
            cmd='git fetch',
            verbose = self.get('verbose'), 
            msg = "Fetch all unknows from the remote").run(cache=False) 
        if result.returncode != 0:
            raise RuntimeError(f"Error: Unable to fetch from the remote")
            sys.exit(1)
            
        # get the name of the default branch       
        [self.props['default_branch'], result] = Gitter(
            cmd=f"gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'",
            verbose = self.get('verbose'), 
            msg = "Get the name of the default branch").run(cache=True)
    
        # get the name of the remote
        [self.props['remote'], result] = Gitter(
            cmd='git remote',
            verbose=self.props['verbose'],
            msg="Get the name of the remote").run(cache=False)        
        

    def collapse(self):
        """Collapse the current branch into a single commit"""
        
        # Get the name of the current branch        
        [self.props['branch_name'], result] = Gitter(
            cmd='git rev-parse --abbrev-ref HEAD',
            verbose=self.get('verbose'),
            msg="Get the name of the current branch").run(cache=False)
        
        # Get the SHA1 of the current branch
        [self.props['SHA1'], result] = Gitter(
            cmd='git rev-parse HEAD',
            verbose=self.props['verbose'],
            msg="Get the SHA1 of the current branch").run(cache=False)
        
        # Get the merge base of the current branch and the default branch
        [self.props['merge_base'], result] = Gitter(
        cmd=f"git merge-base {self.props['branch_name']} {self.props['default_branch']}",
        verbose=self.get('verbose'),
        msg="Get the merge base of the current branch and the default branch").run(cache=False)

        
        # Check if the current branch is the default branch
        if self.get('branch_name') == self.get('default_branch'):
            raise RuntimeError(f"Cannot collapse the default branch ({self.get('branch_name')})")
            sys.exit(1)
            
        # Get the issue number from the branch name
        match = re.match(r'^(\d+).+', self.get('branch_name'))
        if match:
            self.set('issue_number', match.group(1))
        else:
            self.set('issue_number', None)
            print (f"WARNING: The branch name {self.get('branch_name')} does not contain an issue number")
            
            
        # Get the number of commits in the current branch
        [self.props['commit_count'], result] = Gitter(
            cmd=f"git rev-list --count {self.get('branch_name')} ^{self.get('default_branch')}",
            verbose=self.get('verbose'), 
            msg="Get the number of commits in the current branch").run(cache=False)
        
        # get the most recent commit message
        [self.props['commit_message'], result] = Gitter(
            cmd=f"git show -s --format=%B {self.props['branch_name']}",
            verbose=self.props['verbose'],
            msg="Get the commit message of the current branch HEAD").run(cache=False)
        
        # Check if the commit message already contains the issue number
        if self.get('issue_number') != None:
            if not re.search(r'fixed #'+self.get('issue_number'), self.get('commit_message')) and not re.search(r'closed #'+self.get('issue_number'), self.get('commit_message')):
                self.set('new_message', self.get('commit_message') + \
                    f" - closed #{self.get('issue_number')}")
            else:
                self.set('new_message', self.get('commit_message'))
        
        # Check if the collapse is even necessary
        if self.get('commit_count') == '1':
            print(
                "Nothing to collapse. The branch already only contain a single commit")
            if self.props['new_message'] != self.props['commit_message']:
                print("The commit message has been updated and amended.")
                
                [output, result] = Gitter(
                    cmd=f"git commit --amend -m \"{self.props['new_message']}\"",
                    verbose=self.props['verbose'],
                    msg="Amend the commit message").run(cache=False)
                                
                [self.props['new_SHA1'], result] = Gitter(
                    cmd=f"git rev-parse HEAD",
                    verbose=self.props['verbose'],
                    msg="Get the SHA1 of the new commit").run(cache=False)
            else:
                print("Even the commit message is already up to date.")

        # A collapse is necessary
        else:            
            # construct the command to collpase the branch and run it
            [self.props['new_SHA1'], result] = Gitter(
                cmd=f"git commit-tree {self.get('branch_name')}^{{tree}} -p {
                self.get('merge_base')} -m \"{self.get('new_message')}\"",
                verbose=self.get('verbose'),
                msg="Collapse the branch into a single commit").run(cache=False)

            
            # verify that the new commit tree is identical to the old commit
            [output, result] = Gitter(
                cmd=f"git diff-tree --no-commit-id --name-only -r {self.props['SHA1']} {self.props['new_SHA1']}",
                verbose=self.props['verbose'],
                msg="Verify that the new commit tree is identical to the old commit").run(cache=False)
            if output != '':
                raise AssertionError(f"New commit tree ({self.get('new_SHA1')}) is not identical to the old commit tree ({self.get('SHA1')})\n Diff:\n{output}")
                sys.exit(1)

            # move the branch to the new commit
            [output, result] = Gitter(
                cmd=f"git reset {self.props['new_SHA1']}",
                verbose=self.props['verbose'],
                msg="Set the branch to the new commit").run(cache=False)

        
        # Get the SHA1 of the default branch
        [self.props['default_SHA1'], result] = Gitter(
        f"git rev-parse {self.props['default_branch']}",
        verbose=self.props['verbose'],
        msg="Get the SHA1 of the default branch").run(cache=False)
            
        # Check if the default branch is ahead of the merge-base
        if self.get('default_SHA1') != self.get('merge_base'):
            # rebase the default branch            
            print(f"WARNING:\nThe {
                  self.get('default_branch')} branch has commits your branch has never seen. A rebase is required. Do it now!")
    
            
    def set_issue(self, issue_number=int, assign=True):
        """Set the issue number context to work on"""
        self.set('issue_number', issue_number)
        self.set('assign', assign)            
        
        ## check if there is a local branch with the issue number
        [local_branches, result] = Gitter(
            'git branch --format="%(refname:short)"',
            verbose=self.props['verbose'],
            msg=f"Get all local branches").run(cache=False)
        match=False
        for branch in local_branches.split('\n'):          
            if re.match(f"^{issue_number}.+", branch):
                self.set('branch_name', branch)
                [output, result] = Gitter(
                    cmd=f"git checkout {self.props['branch_name']}",
                    verbose=self.props['verbose'],
                    die_on_error=False,
                    msg=f"Switch to the branch {self.get('branch_name')}").run(cache=False)
                if result.returncode != 0:
                    print(f"Error: {result.stderr}", file=sys.stderr)
                    sys.exit(1)
                match=True
                break
            
        if not match:
            ## check if there is a remote branch with the issue number
            [remote_branches, result] = Gitter(
                cmd='git branch -r --format="%(refname:short)"',
                verbose=self.props['verbose'],
                msg=f"Get all remote branches").run(cache=False)
            for branch in remote_branches.split('\n'):
                match_obj = re.match(f"^origin/({issue_number}.+)", branch)
                if match_obj:
                    self.set('branch_name', match_obj.group(1) )
                    [output, result] = Gitter(
                        cmd=f"git checkout -b {self.get('branch_name')} {self.get('remote')}/{self.get('branch_name')}",
                        verbose=self.props['verbose'],
                        msg=f"Switch to the branch {self.props['branch_name']}").run(cache=False)
                    match=True
                    break
        
        if not match:
            ## get the title of the issue
            [self.props['issue_title'], result] = Gitter(
                cmd=f"gh issue view {issue_number} --json title --jq '.title'",
                verbose=self.props['verbose'],
                die_on_error=False,
                msg=f"Get the title of the issue").run(cache=False)
            if result.returncode != 0:
                print(f"Error: Issue {issue_number} not found", file=sys.stderr)
                sys.exit(1)
            
            ## Construct a valid branch name based on the issue number, and the title, replacing spaces with underscores and weed out any chars that aren't allowind in branch names
            self.set('branch_name', f"{issue_number}-{re.sub('[^a-zA-Z0-9_-]', '', re.sub(' ', '_', self.get('issue_title')))}" )
            
            # create a new branch, link it to it's upstream , it's issue issue and then check it out           
            [output, result] = Gitter(
                cmd=f"gh issue develop {issue_number} -b {self.get('default_branch')} -n {self.get('branch_name')} -c" ,
                verbose=self.props['verbose'],
                die_on_error=False,
                msg=f"Get the body of the issue").run(cache=False)
        
        # at this point the branch should exist and is checked out - either through a local branch, a remote branch or a new branch 
        
        if self.get('assign'):
            [output, result] = Gitter(
                cmd=f"gh issue edit {issue_number} --add-assignee '@me'",
                verbose=self.props['verbose'],
                msg=f"Assign @me to the issue").run(cache=False)   
            
        project = Project( verbose=self.get('verbose'))
        issue_url = project.get_url_from_issue(issue=issue_number)
        project.update_field( url=issue_url, field=project.get('workon_field'), field_value=project.get('workon_field_value')  ) 

    def create_issue(self, title=str, body=None):
        """Create a new issue with the title"""
        issue_number = None
        
        [output, result] = Gitter(
            cmd=f"gh issue create --title '{title}' -b '{body}'",
            verbose=self.props['verbose'],
            msg=f"Create a new issue with the title '{title}'").run(cache=False)
        
        match_obj = re.search(r'^https://.*/issues/(\d+)', output, re.MULTILINE)
        if match_obj:
            issue_number = match_obj.group(1)
            return issue_number
        else:
            print("ERROR: Issue number not found", file=sys.stderr)
            
        
    
                  

