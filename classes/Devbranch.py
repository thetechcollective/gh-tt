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
        'new_SHA1': None,
        'new_message': None,
        'git_root': None,
        'workdir': None,
        'default_branch': 'main',
        'remote': 'origin',
        'commit_count': None,
        'verbose': False
    }

    props['workdir'] = os.getcwd()

    def __run_git(self, cmd=str, die_on_error=True, msg=None):
        """Run a git command and return the output"""
        if msg != None:
            msg = f"# {msg}:\n"
        else:
            msg = ""
        self.verbose_print(f"{msg}$ {cmd}\n")
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=True, cwd=self.props['workdir'])
        if die_on_error and not result.returncode == 0:
            raise RuntimeError(f"{result.stderr}")
            sys.exit(1)
        output = result.stdout.strip()
        return output, result
    
    def verbose(self, verbose):
        self.props['verbose'] = verbose
        
    def verbose_print(self, message):
        if self.props['verbose'] == True:
            print(message)
            

    # Instance methods
    def __init__(self, workdir=None, verbose=False):
        self.props['verbose'] = verbose
        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.props['workdir'] = os.path.abspath(workdir)

        [output, result] = self.__run_git(
            'git fetch', 
            msg="Fetch all unknows from the remote")

        [self.props['git_root'], result] = self.__run_git(
            'git rev-parse --show-toplevel', 
            msg="Get the root of the git repository")

        self.__read_context()

    def __read_context(self):
        """Desinged to be called from __init__ to read the branch context in the repo"""

        [self.props['branch_name'], result] = self.__run_git(
            'git rev-parse --abbrev-ref HEAD',
            msg="Get the name of the current branch")

        # Get the SHA1 of the current branch
        [self.props['SHA1'], result] = self.__run_git(
            'git rev-parse HEAD',
            msg="Get the SHA1 of the current branch")

        # Get the issue number
        match = re.match(r'^(\d+).+', self.props['branch_name'])
        if match:
            self.props['issue_number'] = match.group(1)
        else:
            self.props['issue_number'] = None

        # get the most recent commit message
        [self.props['commit_message'], result] = self.__run_git(
            f"git show -s --format=%B {self.props['branch_name']}",
            msg="Get the commit message of the current branch HEAD")

        if self.props['issue_number'] != None:
            if not re.search(r'fixed #'+self.props['issue_number'], self.props['commit_message']) and not re.search(r'closed #'+self.props['issue_number'], self.props['commit_message']):
                self.props['new_message'] = self.props['commit_message'] + \
                    f" - closed #{self.props['issue_number']}"
            else:
                self.props['new_message'] = self.props['commit_message']

        # Get the merge base of the current branch and the default branch
        [self.props['merge_base'], result] = self.__run_git(
            f"git merge-base {self.props['branch_name']} {self.props['default_branch']}",
            msg="Get the merge base of the current branch and the default branch")

        # Get the SHA1 of the default branch
        [self.props['default_SHA1'], result] = self.__run_git(
            f"git rev-parse {self.props['default_branch']}",
            msg="Get the SHA1 of the default branch")

        # Get the number of commits in the current branch
        [self.props['commit_count'], result] = self.__run_git(
            f"git rev-list --count {self.props['branch_name']} ^{self.props['default_branch']}",
            msg="Get the number of commits in the current branch")

    def collapse(self):
        """Collapse the current branch into a single commit"""
        
        if self.props['branch_name'] == self.props['default_branch']:
            raise RuntimeError(f"Cannot collapse the default branch ({
                               self.props['default_branch']}) This feature is limited to works on issue branches (branches that start with an issue number)")
            sys.exit(1)

        # Check if the collapse is even necessary
        if self.props['commit_count'] == '1':
            print(
                "WARNING:\nNothing to collapse. The branch already only contain a single commit")
            if self.props['new_message'] != self.props['commit_message']:
                print("The commit message has been updated.")
                [output, result] = self.__run_git(
                    f"git commit --amend -m \"{self.props['new_message']}\"")
                [[self.props['new_SHA1'], result]] = self.__run_git(
                    f"git rev-parse HEAD")
            else:
                print("Even the commit message is already up to date.")

        # A collapse is necessary
        else:
            # construct the command to collpase the branch and run it
            cmd = f"git commit-tree {self.props['branch_name']}^{{tree}} -p {
                self.props['merge_base']} -m \"{self.props['new_message']}\""
            [self.props['new_SHA1'], result] = self.__run_git(
                cmd,
                msg="Collapse the branch into a single commit")

            # verify that the new commit tree is identical to the old commit
            [output, result] = self.__run_git(
                f"git diff-tree --no-commit-id --name-only -r {self.props['SHA1']} {self.props['new_SHA1']}",
                msg="Verify that the new commit tree is identical to the old commit")
            if output != '':
                raise AssertionError(f"New commit tree ({self.props['new_SHA1']}) is not identical to the old commit tree ({
                                     self.props['SHA1']})\n Diff:\n{output}")
                sys.exit(1)

            # move the branch to the new commit
            [output, result] = self.__run_git(
                f"git reset {self.props['new_SHA1']}",
                msg="Set the branch to the new commit")

        # Check if the default branch is ahead of the merge-base
        if self.props['default_SHA1'] != self.props['merge_base']:
            # rebase the default branch            
            print(f"WARNING:\nThe {
                  self.props['default_branch']} branch has commits your branch has never seen. A rebase is required. Do it now!")
            
    def set_issue(self, issue_number):
        """Set the issue number context to work on"""
        self.props['issue_number'] = issue_number
        
        ## check if there is a local branch with the issue number
        [output, result] = self.__run_git(
            'git branch --format="%(refname:short)"',
            msg=f"Get all local branches")
        match=False
        for branch in output.split('\n'):          
            if re.match(f"^{issue_number}.+", branch):
                self.props['branch_name'] = branch
                [output, result] = self.__run_git(
                    f"git checkout {self.props['branch_name']}",
                    msg=f"Switch to the branch {self.props['branch_name']}")
                match=True
                break
            
        if not match:
            ## check if there is a remote branch with the issue number
            [output, result] = self.__run_git(
                'git branch -r --format="%(refname:short)"',
                msg=f"Get all remote branches")
            for branch in output.split('\n'):
                match_obj = re.match(f"^origin/({issue_number}.+)", branch)
                if match_obj:
                    self.props['branch_name'] = match_obj.group(1)
                    [output, result] = self.__run_git(
                        f"git checkout -b {self.props['branch_name']} {self.props['remote']}/{self.props['branch_name']}",
                        msg=f"Switch to the branch {self.props['branch_name']}")
                    match=True
                    break
        
        if not match:
            ## get the title of the issue
            [self.props['issue_title'], result] = self.__run_git(
                f"gh issue view {issue_number} --json title --jq '.title'",
                die_on_error=False,
                msg=f"Get the title of the issue")
            if result.returncode != 0:
                print(f"Error: Issue {issue_number} not found", file=sys.stderr)
                sys.exit(1)
           ## create a new branch with the issue number, and the title as the branch name, replacing spaces with underscores , and weed out any chars that arn't allowind in branch names
            self.props['branch_name'] = f"{issue_number}-{re.sub('[^a-zA-Z0-9_-]', '', re.sub(' ', '_', self.props['issue_title']))}"
            [output, result] = self.__run_git(
                f"git branch  {self.props['branch_name']} {self.props['default_branch']}",
                msg=f"Create and checkout an issue branch off of the default branch")    
            [output, result] = self.__run_git(
                f"git checkout {self.props['branch_name']}",
                msg=f"Switch to the branch {self.props['branch_name']}")
            
            [output, result] = self.__run_git(
                f"git push --set-upstream {self.props['remote']} {self.props['branch_name']}",
                msg=f"Set the upstream branch") 
            
    def create_issue(self, title):
        """Create a new issue with the title"""
        issue_number = None
        [output, result] = self.__run_git(
            f"gh issue create --title '{title}' -b ''",
            msg=f"Create a new issue with the title '{title}'")
        match_obj = re.search(r'^https://.*/issues/(\d+)', output, re.MULTILINE)
        if match_obj:
            issue_number = match_obj.group(1)
            return issue_number
        else:
            print("ERROR: Issue number not found", file=sys.stderr)
        
    
                  

