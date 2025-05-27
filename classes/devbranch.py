from config import Config
from lazyload import Lazyload
from issue import Issue
from project import Project
from gitter import Gitter
import os
import subprocess
import sys
import re
import asyncio
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

        # Init properties that are not defined in props.json
        self.props = {
            'unstaged_changes': None,
            'staged_changes': None,
            'is_dirty': False,
        }

        self.set('issue_number', self.__validate_issue_branch())

    def __validate_issue_branch(self):
        # Depends on 'init' group being loaded
        """Validate the current branch name to be a valid development branch
        Returns:
            str: The issue number extracted from the branch name
        Raises:
            AssertionError: If the branch name does not start with a valid issue number
        Additional:
            Loads 'init' group from the manifest
        """

        asyncio.run(self._assert_props(['branch_name']))
        match = re.match(r'^(\d+).+', self.get('branch_name'))
        assert match, f"Branch name '{self.get('branch_name')}' does not constitute a valid development branch - Must be prefixed with a valid issue number"
        return f"{match.group(1)}"

    async def __load_details(self):

        if self._details_loaded:
            return

        else:

            # Get the status output from git
            [status_output, _] = await Gitter(
                cmd='git status --porcelain',
                msg="Get the status of the working directory",
                die_on_error=True).run()

            # Parse the status lines
            unstaged = []
            staged = []
            for line in status_output.splitlines():
                if line.startswith('??') or line.startswith(' M'):
                    unstaged.append(line)
                elif line.startswith('M ') or line.startswith('MM') or line.startswith('A '):
                    staged.append(line)

            self.set('unstaged_changes', unstaged)
            self.set('staged_changes', staged)
            self.set('is_dirty',  len(unstaged) > 0 or len(staged) > 0)

            await self.load_prop(
                prop='merge_base',
                cmd=f"git merge-base {self.get('branch_name')} {self.get('default_branch')}",
                msg="Get the merge base of the current branch and the default branch")

            await self.load_prop(
                prop='default_sha1',
                cmd=f"git rev-parse {self.get('default_branch')}",
                msg="Get the SHA1 of the default branch")

            await self.load_prop(
                prop='commit_count',
                cmd=f"git rev-list --count {self.get('branch_name')} ^{self.get('default_branch')}",
                msg="Get the number of commits in the current branch")

            await self.load_prop(
                prop='commit_message',
                cmd=f"git show -s --format=%B {self.get('branch_name')}",
                msg="Get the commit message of the current branch HEAD")

        self._details_loaded = True
        return

    def __validate_commit_message(self):
        # TODO: Get rid of this
        """
        Check if the commit message already contains the issue number, fix it if it doesn't
        """
        commit_message = self.get('commit_message')
        issue_number = self.get('issue_number')

        if re.search(r'(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved) #'+issue_number, commit_message):
            self.set('new_message', commit_message)
            return commit_message
        else:
            self.set('new_message', commit_message +
                     f" - resolves #{issue_number}")
            return self.get('new_message')

    async def __load_squeezed_commit_message(self):
        """
        Build the multiline commit message for the collapsed commit.
        The first line is the issue title, followed by the commit messages
        for each commit on the branch (excluding the merge base).
        """
        await self._assert_props([
            'issue_title',
            'commit_log'
            ])


        # Build the final message
        close_keyword = Config.config()['wrapup']['policies']['close-keyword']
        issue_number = self.get('issue_number')


        # Escape quotes and backticks for safe inclusion in the commit message
        safe_title = self.get('issue_title').replace('"', '\\"').replace('`', '\\`')
        safe_commit_log = self.get('commit_log').replace('"', '\\"').replace('`', '\\`')
        self.set('squeeze_message', f"{safe_title} – {close_keyword} #{issue_number}\n\n{safe_commit_log}")
        return self.get('squeeze_message')

    async def __squeeze(self):
        """
        Squeeze the current branch into a single commit
        """

        # Abort for rebase if we must
        await self._assert_props([
            'merge_base',
            'default_sha1',
            'default_branch'
        ])
        if Config.config()['squeeze']['policies']['abort_for_rebase']:
            if self.get('default_sha1') != self.get('merge_base'):
                print(
                    f"ERROR: The {self.get('default_branch')} branch has commits your branch has never seen. A rebase is required. Do it now!", file=sys.stderr)
                sys.exit(1)

        # check if the working directory is dirty
        # assert 'status', 'is_dirty', 'unstaged_changes' and 'staged_changes'
        await self._load_status()
        if self.get('is_dirty'):
            # check if dirty is allowed
            if Config.config()['squeeze']['policies']['allow-dirty'] == False:
                print("ERROR: The working directory is not clean:", file=sys.stderr)
                print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                print("Commit or stash the changes.", file=sys.stderr)

                sys.exit(1)
            # check if staged changes are allowed
            else:
                if Config.config()['squeeze']['policies']['allow-staged'] == False and len(self.get('staged_changes')) > 0:
                    print("ERROR: There are staged changes:", file=sys.stderr)
                    print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                    print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                    print("Commit or stash the changes.", file=sys.stderr)
                    sys.exit(1)

                # check if we should warn about dirty working directory
                if not Config.config()['squeeze']['policies']['quiet'] == True:
                    print("WARNING: The working directory is not clean:",
                          file=sys.stderr)
                    print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                    print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                    print(
                        "The branch will be squeezed, but the changes in the files listed above will not be included in the commit.", file=sys.stderr)

        await self.__load_squeezed_commit_message()

        #await self._load_prop(
        #    prop='squeeze_sha1',
        #    cmd=f"git commit-tree {self.get('branch_name')}^{{tree}} -p {self.get('merge_base')} -m \"{squeeze_message}\"",
        #    msg="Collapse the branch into a single commit")

        await self._assert_props(['squeeze_sha1'])

        await self.__compare_before_after_trees()

        return self.get('squeeze_sha1')

    def __workspace_is_clean(self):
        # check if status is clean
        value = None
        result = None
        [val, result] = Gitter(
            cmd='git status --porcelain',
            die_on_error=False,
            msg="Check if the status is clean").run()

        if value != '':
            print(
                f"ERROR: The working directory is not clean:\n{value}\n\nPlease commit or stash your changes before delivering the issue")
            sys.exit(1)
        return True

    async def __rebase(self, autostash=True):
        """
        Rebase the branch to the default branch
        """
        await self.__load_details()

        autostash_switch = ''
        if autostash:
            autostash_switch = '--autostash '

        [_, result] = await Gitter(
            cmd=f"git rebase {autostash_switch}{self.get('remote')}/{self.get('default_branch')}",
            die_on_error=False,
            msg="Rebase the branch").run()
        if result.returncode != 0:
            # abort the rebase
            [_, _] = Gitter(
                cmd="git rebase --abort",
                msg="Abort the rebase").run()
            print(
                f"ERROR: Could not rebase the branch\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        return True

    async def __push(self, force=False):
        # push the branch to the remote
        force_switch = ''
        if force == True:
            force_switch = '--force-with-lease'

        [output, result] = Gitter(
            cmd=f"git push {force_switch}",
            msg="Push the branch to the remote").run()

        return True

    async def __compare_before_after_trees(self):
        """
        Verify that the new commit tree on the collapsed branch is identical to the old commit
        """

        sha1 = self.get('sha1')
        squeeze_sha1 = self.get('squeeze_sha1')
        [output, result] = await Gitter(
            cmd=f"git diff-tree --no-commit-id --name-only -r {sha1} {squeeze_sha1}",
            msg="Verify that the new squeezed commit tree is identical to the one on the issue branch").run()

        if output != '':
            print(
                f"WARNING:\nThe squeezed commit tree ({squeeze_sha1}) is not identical to the one on the issue branch ({sha1})\n Diff:\n{output}")
            return False
        else:
            return True

    def __reset_branch(self, squeeze_sha1=None, prefix=None):
        """
        Reset the current branch to the new commit
        If prefix is set, create a new branch with the same name as the current branch, but prefixed with prefix"""

        if squeeze_sha1 == None:
            squeeze_sha1 = self.get('squeeze_sha1')

        branch_name = self.get('branch_name')

        if prefix is not None:
            branch_name = f"{prefix}{branch_name}"

        value = None
        result = None
        [value, result] = Gitter(
            cmd=f"git branch -f {branch_name} {squeeze_sha1}",
            msg=f"Set the branch '{branch_name}' to the new commit").run()
        return squeeze_sha1

    async def __check_rebase(self):
        # Get the SHA1 of the default branch
        await self.__load_details()

        # Check if the default branch is ahead of the merge-base
        if self.get('default_sha1') != self.get('merge_base'):
            # rebase the default branch
            print(
                f"WARNING:\nThe {self.get('default_branch')} branch has commits your branch has never seen. A rebase is required. Do it now!")
            return False
        else:
            return True

    async def collapse(self):
        """Collapse the current branch into a single commit"""

        await self.__load_details()

        # Check if the current branch is the default branch
        if self.get('branch_name') == self.get('default_branch'):
            print(
                f"ERROR: Cannot collapse the default branch: ({self.get('branch_name')})\nSwitch to a development branch", file=sys.stderr)
            sys.exit(1)

        # check if status is clean
        self.__workspace_is_clean()  # will exit if not clean

        # Rebase the branch to the remote
        self.__rebase()  # will exit if rebase fails

        # Get the number of commits in the current branch
        commit_count = self.get('commit_count')

        # Check if the commit message already contains the issue number
        issue_number = self.get('issue_number')

        # Check if the commit message already contains the valid issue reference
        new_message = self.__validate_commit_message()

        # TODO don't do this check, just collapse!
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

            # TODO Set then branch to a ready branch
            # move the branch to the new commit
            self.__reset_branch(prefix=Config.config()[
                                'wrapup']['policies']['branch_prefix'])

        # push the branch to the remote
        # TODO be sure to push the right branch - if the ready branch is used, that's the one that should be pushed
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

    def wrapup(self, message:str):
        """Mapped to the 'wrapup' subcommand."""
        # Implements similar behavior to the "note-this" alias:
        # - Stage all changes if nothing is staged
        # - Commit with message "<message> #<issue_number>"
        # - Push the branch

        
        asyncio.run(self._load_status())

        if not self.get('is_dirty'):
            print("Nothing to commit. The working directory is clean.")
            return

        # If nothing is staged, stage all changes
        if not len(self.get('staged_changes')) > 0:
            # Stage all changes if nothing is staged
            [_, _] = asyncio.run(Gitter(
                cmd="git add -A",
                msg="Nothin is staged. Staging all changes").run()
            )

        
        # TODO - list staged files in this commit
        # git diff --name-only --cached
        
        msg = f"{message} - #{self.get('issue_number')}"

        [_, result] = asyncio.run( Gitter(
            cmd=f'git commit -m "{msg}"',
            msg="Commit changes").run()
        )

        [_, _] = asyncio.run( Gitter(
            cmd="git push",
            msg="Push branch").run()
        )

        print(f"\n\n👍\nBranch has got a new commit that mentions issue '{self.get('issue_number')} and it's pushed")
        return True


    async def _load_status(self):
        """Load the status of the current branch sets the following properties:
        - 'status': The output of `git status --porcelain`
        - 'is_dirty': True if there are unstaged or staged changes
        - 'unstaged_changes': List of unstaged changes
        - 'staged_changes': List of staged changes"""

        if self.get('is_dirty') and self.get('unstaged_changes') and self.get('staged_changes'):
            # If the status is already loaded, return
            return

        await self._assert_props(['status'])
        self.props['unstaged_changes'] = []
        self.props['staged_changes'] = []
        for line in self.get('status').splitlines():
            if line.startswith('??') or line.startswith(' M'):
                self.props['unstaged_changes'].append(line)
            elif line.startswith('M ') or line.startswith('MM') or line.startswith('A '):
                self.props['staged_changes'].append(line)
        self.set('is_dirty',  len(self.props['unstaged_changes']) > 0 or len(
            self.props['staged_changes']) > 0)

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

    def deliver(self):
        """Mapped to the 'deliver' subcommand."""

        squeeze_sha = asyncio.run(self.__squeeze())
        remote = self.get('remote')
        branch_name = self.get('branch_name')
        ready_prefix = Config.config()['deliver']['policies']['branch_prefix']
        
        
        [output, result] = asyncio.run( Gitter(
            cmd=f"git push --force-with-lease {remote} {squeeze_sha}:refs/heads/{ready_prefix}/{branch_name}",
            die_on_error=True,
            msg="Push the squeezed sha to the remase as a 'ready' branch").run()
        )

        print(f"\n\n👍\nBranch '{branch_name}' has been squeezed into one commit; '{squeeze_sha[:7]}' and pushed to {remote} as '{ready_prefix}/{branch_name}'")

        return squeeze_sha
