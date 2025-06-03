from config import Config
from lazyload import Lazyload
from responsibles import Responsibles
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
        self.set('unstaged_changes', None)
        self.set('staged_changes', None)
        self.set('is_dirty', None)
        self.set('issue_number', None)

    async def _load_issue_number(self):

        await self._assert_props(['branch_name'])
        match = re.match(r'^(\d+).+', self.get('branch_name'))
        if not match:
            self.set('issue_number', None)
            return False
        
        self.set('issue_number',f"{match.group(1)}")
        return True

    async def __load_squeezed_commit_message(self):
        """
        Build the multiline commit message for the collapsed commit.
        The first line is the issue title, followed by the commit messages
        for each commit on the branch (excluding the merge base).
        """
        await self._load_issue_number()

        await self._assert_props([
            'issue_title',
            'commit_log'
        ])

        # Build the final message
        close_keyword = Config.config()['wrapup']['policies']['close-keyword']
        issue_number = self.get('issue_number')

        # Escape quotes and backticks for safe inclusion in the commit message
        safe_title = self.get('issue_title').replace(
            '"', '\\"').replace('`', '\\`')
        safe_commit_log = self.get('commit_log').replace(
            '"', '\\"').replace('`', '\\`')
        self.set('squeeze_message',
                 f"{safe_title} – {close_keyword} #{issue_number}\n\n{safe_commit_log}")
        return self.get('squeeze_message')

    async def __squeeze(self):
        """
        Squeeze the current branch into a single commit
        """

        await self._load_status()

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

        # await self._load_prop(
        #    prop='squeeze_sha1',
        #    cmd=f"git commit-tree {self.get('branch_name')}^{{tree}} -p {self.get('merge_base')} -m \"{squeeze_message}\"",
        #    msg="Collapse the branch into a single commit")

        await self._assert_props(['squeeze_sha1'])

        await self.__compare_before_after_trees()

        return self.get('squeeze_sha1')

    async def _push(self, force=False):
        # push the branch to the remote
        force_switch = ''
        if force == True:
            force_switch = '--force-with-lease'

        [output, result] = await Gitter(
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

    def __develop(self, issue_number=int, branch_name=str):
        """Develop on the issue branch, creating a new branch if needed
        Args:
            issue_number (int): The issue number to develop on
            branch_name (str): The name of the branch to develop on
        """
        
        [output, result] = asyncio.run(Gitter(
            cmd=f"gh issue develop {issue_number} -b {self.get('default_branch')} -n {self.get('branch_name')} -c",
            msg=f"gh develop {issue_number} on new branch {branch_name}").run()
        )

    def __reuse_issue_branch(self, issue_number=int):
        """Check if there is a local or remote branch with the issue number and switch to it
        Args:
            issue_number (int): The issue number to check for
        Returns:
            bool: True if a branch was found and switched to, False otherwise
        """
        # check if there is a local branch with the issue number
        [local_branches, result] = asyncio.run(Gitter(
            cmd='git branch --format="%(refname:short)"',
            msg=f"Get all local branches").run()
        )
        match = False
        for branch in local_branches.split('\n'):
            if re.match(f"^{issue_number}.+", branch):
                self.set('branch_name', branch)
                [output, result] = asyncio.run(Gitter(
                    cmd=f"git checkout {self.get('branch_name')}",
                    die_on_error=False,
                    msg=f"Switch to the branch {self.get('branch_name')}").run()
                )
                if result.returncode != 0:
                    print(f"Error: {result.stderr}", file=sys.stderr)
                    sys.exit(1)
                match = True
                break

        if not match:
            # check if there is a remote branch with the issue number
            [remote_branches, result] = asyncio.run(Gitter(
                cmd='git branch -r --format="%(refname:short)"',
                msg=f"Get all remote branches").run()
            )
            for branch in remote_branches.split('\n'):
                match_obj = re.match(f"^origin/({issue_number}.+)", branch)
                if match_obj:
                    self.set('branch_name', match_obj.group(1))
                    [output, result] = asyncio.run(Gitter(
                        cmd=f"git checkout -b {self.get('branch_name')} {self.get('remote')}/{self.get('branch_name')}",
                        msg=f"Switch to the branch {self.props['branch_name']}").run()
                    )
                    match = True
                    break
        return match

    def wrapup(self, message: str):
        """Mapped to the 'wrapup' subcommand in the main program"""

        asyncio.run(self._load_issue_number())
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
            asyncio.run(self._load_status(reload=True))

        msg = f"{message} - #{self.get('issue_number')}"

        [me,_] = asyncio.run(Gitter(
            cmd="gh api user --jq '.login'",
            msg="Get my GitHub handle").run()
        )

        change_list = self._get_pretty_changes()
        responsibles = Responsibles().responsibles_as_markdown(
            changeset=change_list,
            exclude=[f"@{me}"]
        )
        

        [_, result] = asyncio.run(Gitter(
            cmd=f'git commit -m "{msg}"',
            msg="Commit changes").run()
        )

        asyncio.run(self._push(force=True))


        responsibles_alert = ''
        if responsibles:
            # Add the responsibls to a comment on the issue
            [_, _] = asyncio.run(Gitter(
                cmd=f"gh issue comment {self.get('issue_number')} --body '{responsibles}'",
                msg="Add responsibles to the issue").run()
            )

            responsibles_alert = f"\n\n🔔 You touched on files that have named responsibles {responsibles}\n\n"


        print(
            f"\n\n👍 Branch has got a new commit that mentions issue '#{self.get('issue_number')}' and it's pushed\n{responsibles_alert}💡 Try to run: gh browse {self.get('issue_number')}")
        return True

    async def _load_status(self, reload: bool = False):
        """Load the status of the current branch sets the following properties:
        - 'status': The output of `git status --porcelain`
        - 'is_dirty': True if there are unstaged or staged changes
        - 'unstaged_changes': List of unstaged changes
        - 'staged_changes': List of staged changes"""

        if not reload: # Not in force reload mode
            if self.get('is_dirty') and self.get('unstaged_changes') and self.get('staged_changes'):
                # If the status is already loaded, return
                return

        await self._assert_props(['status'])

        if reload:
            await self._force_prop_reload('status')

        self.props['unstaged_changes'] = []
        self.props['staged_changes'] = []
        for line in self.get('status').splitlines():
            if line.startswith('??') or line.startswith(' M'):
                self.props['unstaged_changes'].append(line)
            elif line.startswith('M ') or line.startswith('MM') or line.startswith('A '):
                self.props['staged_changes'].append(line)
        self.set('is_dirty',  len(self.props['unstaged_changes']) > 0 or len(
            self.props['staged_changes']) > 0)
        
    def _get_pretty_changes(self, staged: bool = True, unstaged: bool = False):
        """Get a pretty formatted list of changes
        
        Args:
            staged (bool): If True, include staged changes
            unstaged (bool): If True, include unstaged changes
        Returns:
            list: A list of changes with the tailing ' M', 'MM', 'A ' or '??' removed
        """
        asyncio.run(self._assert_props(['status']))
        asyncio.run(self._load_status())
        changes = []
        if staged:
            changes.extend(self.get('staged_changes'))
        if unstaged:
            changes.extend(self.get('unstaged_changes'))

        ## Go through all items and remove the tailing ' M', 'MM', 'A ' or '??' 
        changes = [re.sub(r'^\s*([?M]+|A\s+)', '', change) for change in changes]
        # Remove leading whitespace
        changes = [change.lstrip() for change in changes]
        return changes

    def set_issue(self, issue_number=int, assign=True):
        """Set the issue number context to work on"""

        asyncio.run(self._assert_props(['remote', 'default_branch']))


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

        [output, result] = asyncio.run(Gitter(
            cmd=f"git push --force-with-lease {remote} {squeeze_sha}:refs/heads/{ready_prefix}/{branch_name}",
            die_on_error=True,
            msg="Push the squeezed sha to the remote as a 'ready' branch").run()
        )

        print(
            f"\n\n👍\nBranch '{branch_name}' has been squeezed into one commit; '{squeeze_sha[:7]}' and pushed to {remote} as '{ready_prefix}/{branch_name}'")

        return squeeze_sha
