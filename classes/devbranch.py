from lazyload import Lazyload
from issue import Issue
from project import Project
from gitter import Gitter
import os
import subprocess
import sys
import re
from datetime import datetime

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Devbranch(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    # Instance methods
    def __init__(self, workdir=None, verbose=False):
        super().__init__()

        self.set('workdir', os.getcwd())
        self.set('verbose', verbose)
        self.set('default_branch', None)
        self.set('remote', None)
        self.set('branch_name', None)
        self.set('sha1', None)
        self.set('issue_number', None)
        self.set('merge_base', None)
        self.set('commit_count', None)
        self.set('commit_message', None)
        self.set('new_message', None)
        self.set('squeeze_sha1', None)
        self.set('default_sha1', None)

        if workdir:
            # check if the directory exists
            if not os.path.exists(workdir):
                raise FileNotFoundError(f"Directory {workdir} does not exist")
                sys.exit(1)
            self.set('workdir', os.path.abspath(workdir))

        # Git fetch
        [output, result] = Gitter(
            cmd='git fetch',
            msg="Fetch all unknows from the remote").run()
        if result.returncode != 0:
            raise RuntimeError(f"Error: Unable to fetch from the remote")
            sys.exit(1)

        # get the name of the default branch
        value = None
        result = None
        [value, result] = Gitter(
            cmd=f"gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'",
            msg="Get the name of the default branch").run(cache=True)
        self.set('default_branch', value)

        # get the name of the remote
        value = None
        result = None
        [value, result] = Gitter(
            cmd='git remote',
            msg="Get the name of the remote").run()
        self.set('remote', value)

        # Get the name of the current branch
        value = None
        result = None
        [value, result] = Gitter(
            cmd='git rev-parse --abbrev-ref HEAD',
            msg="Get the name of the current branch").run()
        self.set('branch_name', value)

        # Set the issue number from the branch name
        match = re.match(r'^(\d+).+', self.get('branch_name'))
        if match:
            self.set('issue_number', f"{match.group(1)}")

    def __get_branch_sha1(self):
        # Get the SHA1 of the current branch
        keyname = 'sha1'
        value = self.get(keyname)
        if value:
            return value

        [value, result] = Gitter(
            cmd='git rev-parse HEAD',
            workdir=self.get('workdir'),

            msg="Get the SHA1 of the current branch").run()

        self.set(keyname, value)
        return self.get(keyname)

    def __get_merge_base(self):
        # Get the merge base of the current branch and the default branch
        keyname = 'merge_base'
        value = self.get(keyname)
        if value:
            return value

        branch_name = self.get('branch_name')
        default_branch = self.get('default_branch')

        [value, result] = Gitter(
            cmd=f"git merge-base {branch_name} {default_branch}",
            workdir=self.get('workdir'),

            msg="Get the merge base of the current branch and the default branch").run()

        self.set(keyname, value)
        return self.get(keyname)

    def __get_commit_count(self):
        # Get the number of commits in the current branch
        keyname = 'commit_count'
        value = self.get(keyname)
        if value:
            return value

        branch_name = self.get('branch_name')
        default_branch = self.get('default_branch')

        [value, result] = Gitter(
            cmd=f"git rev-list --count {self.get('branch_name')} ^{self.get('default_branch')}",
            workdir=self.get('workdir'),

            msg="Get the number of commits in the current branch").run()

        self.set(keyname, value)
        return self.get(keyname)

    def __get_commit_message(self):
        # Get the commit message of the HEAD of the current branch
        keyname = 'commit_message'
        value = self.get(keyname)
        if value:
            return value

        branch_name = self.get('branch_name')

        [value, result] = Gitter(
            cmd=f"git show -s --format=%B {branch_name}",
            workdir=self.get('workdir'),

            msg="Get the commit message of the current branch HEAD").run()

        self.set(keyname, value)
        return self.get(keyname)

    def __validate_commit_message(self):
        # Check if the commit message already contains the issue number , fix it if it doesn't
        commit_message = self.__get_commit_message()
        issue_number = self.get('issue_number')

        if re.search(r'(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved) #'+issue_number, commit_message):
            self.set('new_message', commit_message)
            return commit_message
        else:
            self.set('new_message', commit_message +
                     f" - resolves #{issue_number}")
            return self.get('new_message')

    def __squeeze(self):
        # Squeeze the current branch into a single commit
        keyname = 'squeeze_sha1'
        value = None
        branch_name = self.get('branch_name')
        merge_base = self.__get_merge_base()
        new_message = self.__validate_commit_message()

        [value, result] = Gitter(
            cmd=f"git commit-tree {branch_name}^{{tree}} -p {merge_base} -m \"{new_message}\"",
            workdir=self.get('workdir'),

            msg="Collapse the branch into a single commit").run()

        self.set(keyname, value)
        return self.get(keyname)
    
    def __workspace_is_clean(self):
        # check if status is clean
        [output, result] = Gitter(
            cmd='git status --porcelain',
            die_on_error=False,
            msg="Check if the status is clean").run()

        if output != '':
            print(
                f"ERROR: The working directory is not clean:\n{output}\n\nPlease commit or stash your changes before delivering the issue")
            sys.exit(1)
        return True        

    def __rebase(self):
        # Rebase the branch to the remote
        [output, result] = Gitter(
            cmd="git rebase",
            die_on_error=False,
            msg="Rebase the branch").run()
        if result.returncode != 0:
            print(
                f"ERROR: Could not rebase the branch\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        return True  
    
    def __push(self, force=False):
        # push the branch to the remote
        force_switch = ''   
        if force == True:
            force_switch = '--force'
            
        [output, result] = Gitter(
            cmd=f"git push {force_switch}",
            msg="Push the branch to the remote").run()    
        
        return True          

    def __compare_before_after_trees(self):

        sha1 = self.get('sha1')
        squeeze_sha1 = self.get('squeeze_sha1')
        [output, result] = Gitter(
            cmd=f"git diff-tree --no-commit-id --name-only -r {sha1} {squeeze_sha1}",

            msg="Verify that the new commit tree is identical to the old commit").run()
        if output != '':
            print(
                f"WARNING:\nNew commit tree ({sha1}) is not identical to the old commit tree ({squeeze_sha1})\n Diff:\n{output}")
            return False
        else:
            return True

    def __reset_branch(self, squeeze_sha1):
        [output, result] = Gitter(
            cmd=f"git reset {squeeze_sha1}",

            workdir=self.get('workdir'),
            msg="Set the branch to the new commit").run()
        return squeeze_sha1

    def __check_rebase(self):
        # Get the SHA1 of the default branch
        [default_sha1, result] = Gitter(
            f"git rev-parse {self.get('default_branch')}",
            msg="Get the SHA1 of the default branch").run()
        self.set('default_sha1', default_sha1)

        # Check if the default branch is ahead of the merge-base
        if default_sha1 != self.get('merge_base'):
            # rebase the default branch
            print(f"WARNING:\nThe {self.get('default_branch')} branch has commits your branch has never seen. A rebase is required. Do it now!")
            return False
        else:
            return True

    def collapse(self):
        """Collapse the current branch into a single commit"""

        # Check if the current branch is the default branch
        if self.get('branch_name') == self.get('default_branch'):
            print(
                f"ERROR: Cannot collapse the default branch: ({self.get('branch_name')})\nSwitch to a development branch", file=sys.stderr)
            sys.exit(1)

        # check if status is clean
        self.__workspace_is_clean() # will exit if not clean

        # Rebase the branch to the remote
        self.__rebase() # will exit if rebase fails
        
        # Get the SHA1 of the current branch
        sha1 = self.__get_branch_sha1()

        # Get the merge base of the current branch and the default branch
        merge_base = self.__get_merge_base()

        # Get the number of commits in the current branch
        commit_count = self.__get_commit_count()

        # get the most recent commit message
        commit_message = self.__get_commit_message()

        # Check if the commit message already contains the issue number
        issue_number = self.get('issue_number')

        # Check if the commit message already contains the valid issue reference
        new_message = self.__validate_commit_message()

        # Check if the collapse is even necessary
        if commit_count == '1':
            print(
                "Nothing to collapse. The branch already only contain a single commit")
            if self.props['new_message'] != self.props['commit_message']:
                print("The commit message has been updated and amended.")

                [output, result] = Gitter(
                    cmd=f"git commit --amend -m \"{self.props['new_message']}\"",

                    msg="Amend the commit message").run()

                [self.props['squeeze_sha1'], result] = Gitter(
                    cmd=f"git rev-parse HEAD",

                    msg="Get the SHA1 of the new commit").run()
            else:
                print("Even the commit message is already up to date.")

        # A collapse is necessary
        else:
            squeeze_sha1 = self.__squeeze()

            # verify that the new commit tree is identical to the old commit
            is_the_same = self.__compare_before_after_trees()

            if not is_the_same:
                raise AssertionError(
                    f"Before and after the squeeze commit trees differ")
                sys.exit(1)

            # move the branch to the new commit
            self.__reset_branch(squeeze_sha1)
        
        # push the branch to the remote
        self.__push(force=True)
        
#        print(f"Branch {self.get('branch_name')} has been collapsed into a single commit (was: {self.get('sha1')[:7]} now: {self.get('squeeze_sha1')[:7]})")




    def __develop(self, issue_number=int, branch_name=str):
        # create a new branch, link it to it's upstream , it's issue issue and then check it out
        [output, result] = Gitter(
            cmd=f"gh issue develop {issue_number} -b {self.get('default_branch')} -n {branch_name} -c",
            msg=f"gh develop {issue_number} on new branch {branch_name}").run()

    def __reuse_issue_branch(self, issue_number=int):
        # check if there is a local branch with the issue number
        [local_branches, result] = Gitter(
            cmd='git branch --format="%(refname:short)"',
            msg=f"Get all local branches").run()
        match = False
        for branch in local_branches.split('\n'):
            if re.match(f"^{issue_number}.+", branch):
                self.set('branch_name', branch)
                [output, result] = Gitter(
                    cmd=f"git checkout {self.get('branch_name')}",
                    die_on_error=False,
                    msg=f"Switch to the branch {self.get('branch_name')}").run()
                if result.returncode != 0:
                    print(f"Error: {result.stderr}", file=sys.stderr)
                    sys.exit(1)
                match = True
                break

        if not match:
            # check if there is a remote branch with the issue number
            [remote_branches, result] = Gitter(
                cmd='git branch -r --format="%(refname:short)"',
                msg=f"Get all remote branches").run()
            for branch in remote_branches.split('\n'):
                match_obj = re.match(f"^origin/({issue_number}.+)", branch)
                if match_obj:
                    self.set('branch_name', match_obj.group(1))
                    [output, result] = Gitter(
                        cmd=f"git checkout -b {self.get('branch_name')} {self.get('remote')}/{self.get('branch_name')}",
                        msg=f"Switch to the branch {self.props['branch_name']}").run()
                    match = True
                    break
        return match

    def set_issue(self, issue_number=int, assign=True):
        """Set the issue number context to work on"""
        self.set('issue_number', issue_number)
        self.set('assign', assign)
        issue = Issue(number=issue_number)

        reuse = self.__reuse_issue_branch(issue_number=issue_number)
        if not reuse:
            # Construct a valid branch name based on the issue number, and the title, replacing spaces with underscores and weed out any chars that aren't allowind in branch names
            issue_title = issue.get('title')
            branch_valid_title = re.sub(
                '[^a-zA-Z0-9_-]', '', re.sub(' ', '_', issue_title))
            branch_name = f"{issue_number}-{branch_valid_title}"
            self.set('branch_name', branch_name)
            self.__develop(issue_number=issue_number, branch_name=branch_name)

        # at this point the branch should exist and is checked out - either through a local branch, a remote branch or a new branch

        # TODO Update the data used for metrics: 1) assignee, 2) add to project 3) update project field

        # assign the issue to the current user
        if self.get('assign'):
            issue.assign(assignee='@me')

        # add the issue to the project and set the Status to "In Progess"
        project = Project()
        workon_field = project.get('workon_field')
        workon_field_value = project.get('workon_field_value')
        # TODO get the values from the config
        project.update_field(url=issue.get(
            'url'), field=workon_field, field_value=workon_field_value)

        if not reuse:
            # Get 'today' in YYYY-MM-DD format
            today = datetime.today().strftime('%Y-%m-%d')
            project.update_field(url=issue.get(
                'url'), field='Start', field_value=today, field_type='Date')

    def deliver(self, title=None):
        """Create the pull request for the current issue"""

        issue = Issue(number=self.get('issue_number'))

        if title == None:
            title = issue.get('title')

        # Create a pull request for the current branch
        [output, result] = Gitter(
            cmd=f"gh pr create --title '{title}' --body '' --base {self.get('default_branch')} --assignee '@me'",
            die_on_error=False,
            msg="Create a pull request for the current branch").run()

        # Get the last line of the output, it contains the URL of the pull request
        # and update self.props['pull_request_url']
        # but die if the last line does not contain the URL
        success = False
        if result.returncode == 0:
            match_obj = re.search(
                r'^https://.*/pull/(\d+)', output, re.MULTILINE)
            if match_obj:
                self.set('pull_request_url', match_obj.group(0))
                success = True
        # If a pull request already exists, it will be returned in the stderr
        # so we need to check the stderr for the URL
        else:
            match_obj = re.search(r'^https://.*/pull/(\d+)',
                                  result.stderr.strip(), re.MULTILINE)
            if match_obj:
                self.set('pull_request_url', match_obj.group(0))
                success = True

        if not success:
            print(
                f"ERROR: Could not create the pull request\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        project = Project()

        project.update_field(url=issue.get('url'), field=project.get(
            'deliver_field'), field_value=project.get('deliver_field_value'))

        print(f"{self.get('pull_request_url')}")
        return self.get('pull_request_url')
