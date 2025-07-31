import asyncio
import re
import subprocess
import sys

from gh_tt.classes.config import Config
from gh_tt.classes.issue import Issue
from gh_tt.classes.lazyload import Lazyload
from gh_tt.classes.project import Project
from gh_tt.classes.responsibles import Responsibles


class Devbranch(Lazyload):
    """Class used to represent the Devbranch for a development contribution"""

    # Instance methods
    def __init__(self):
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

    def __load_squeezed_commit_message(self):
        """
        Build the multiline commit message for the collapsed commit.
        The first line is the issue title, followed by the commit messages
        for each commit on the branch (excluding the merge base).
        """
        asyncio.run(self._load_issue_number())

        asyncio.run(self._assert_props([
            'issue_title',
            'commit_log'
        ]))

        # Build the final message
        close_keyword = Config.config()['squeeze']['policies']['close-keyword']
        issue_number = self.get('issue_number')

        # Escape quotes and backticks for safe inclusion in the commit message
        safe_title = self.get('issue_title').replace(
            '"', '\\"').replace('`', '\\`')
        safe_commit_log = self.get('commit_log').replace(
            '"', '\\"').replace('`', '\\`')
        self.set('squeeze_message',
                 f"{safe_title} - {close_keyword} #{issue_number}\n\n{safe_commit_log}")
        return self.get('squeeze_message')

    def __squeeze(self):
        """
        Squeeze the current branch into a single commit
        """

        self._load_status()

        # Abort for rebase if we must
        asyncio.run(self._assert_props([
            'merge_base',
            'default_sha1',
            'default_branch'
        ]))
        if Config.config()['squeeze']['policies']['abort_for_rebase'] and self.get('default_sha1') != self.get('merge_base'):
            print(f"⛔️ ERROR: The '{self.get('default_branch')}' branch has commits your branch has never seen. A rebase is required.", file=sys.stderr)
            print(f"💡 Run: git rebase {self.get('remote')}/{self.get('default_branch')}  (you may - or may not - need to stash or commit your changes first)", file=sys.stderr)            
            if self.get('is_dirty'):
                print("⚠️  Psst: Your workspace is dirty, so you must stash or commit your changes first)", file=sys.stderr)
            sys.exit(1)

        # check if the working directory is dirty
        # assert 'status', 'is_dirty', 'unstaged_changes' and 'staged_changes'
        if self.get('is_dirty'):
            # check if dirty is allowed
            if not Config.config()['squeeze']['policies']['allow-dirty']:
                print("⛔️ ERROR: The working directory is not clean:", file=sys.stderr)
                print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                print("Commit or stash the changes.", file=sys.stderr)

                sys.exit(1)
            # check if staged changes are allowed
            else:
                if not Config.config()['squeeze']['policies']['allow-staged'] and len(self.get('staged_changes')) > 0:
                    print("⛔️ ERROR: There are staged changes:", file=sys.stderr)
                    print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                    print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                    print("Commit or stash the changes.", file=sys.stderr)
                    sys.exit(1)

                # check if we should warn about dirty working directory
                if Config.config()['squeeze']['policies']['quiet']:
                    print("⚠️  WARNING: The working directory is not clean:",
                          file=sys.stderr)
                    print('\n'.join(self.get('unstaged_changes')), file=sys.stderr)
                    print('\n'.join(self.get('staged_changes')), file=sys.stderr)
                    print(
                        "The branch will be squeezed, but the changes in the files listed above will not be included in the commit.", file=sys.stderr)

        self.__load_squeezed_commit_message()

        asyncio.run(self._assert_props(['squeeze_sha1']))

        self.__compare_before_after_trees()

        return self.get('squeeze_sha1')

    def _push(self, *, force=False):
        # push the branch to the remote

        _ = asyncio.run(self._run("git_push", {
            "force_switch": "--force-with-lease" if force else ""
        }))

        return True

    def __compare_before_after_trees(self):
        """
        Verify that the new commit tree on the collapsed branch is identical to the old commit
        """
        asyncio.run(self._assert_props(['sha1', 'squeeze_sha1']))

        sha1 = self.get('sha1')
        squeeze_sha1 = self.get('squeeze_sha1')
        diff = asyncio.run(self._run('compare_trees'))

        if diff != '':
            print(
                f"😱 FATAL:\nThe squeezed commit tree ({squeeze_sha1}) is not identical to the one on the issue branch ({sha1})\n Diff:\n{diff}", file=sys.stderr)
            sys.exit(1)
        
        return True

    def __develop(self):
        """Develop on the issue branch, creating a new branch if needed"""
        
        asyncio.run(self._assert_props(['issue_number', 'default_branch', 'branch_name']))
        asyncio.run(self._run("develop_on_branch"))

    async def __reuse_issue_branch(self, issue_number=int):
        """Check if there is a local or remote branch with the issue number and switch to it
        Args:
            issue_number (int): The issue number to check for
        Returns:
            bool: True if a branch was found and switched to, False otherwise
        """
        await self._assert_props(['local_branches', 'remote_branches'])

        match = False
        for branch in self.get('local_branches').split('\n'):
            if re.match(f"^{issue_number}.+", branch):
                self.set('branch_name', branch)
                try:
                    await self._run(prop='checkout_local_branch', die_on_error=False)
                except subprocess.CalledProcessError as e:
                    print(f"⛔️ ERROR:Failed to checkout local branch: {e}", file=sys.stderr)
                    sys.exit(1)
                match = True
                break

        if not match:
            # check if there is a remote branch with the issue number

            for branch in self.get('remote_branches').split('\n'):
                match_obj = re.match(f"^origin/({issue_number}.+)", branch)
                if match_obj:
                    self.set('branch_name', match_obj.group(1))
                    await self._run('checkout_remote_branch')
                    match = True
                    break
        return match

    def wrapup(self, message: str):
        """Mapped to the 'wrapup' subcommand in the main program"""

        asyncio.run(self._load_issue_number())
        self._load_status()
        asyncio.run(self._assert_props(['me', 'merge_base', 'remote_sha1', 'default_sha1' ]))

        if Config.config()['wrapup']['policies']['warn_about_rebase'] and self.get('merge_base') != self.get('default_sha1'):
            print(
                f"⚠️  WARNING: The '{self.get('default_branch')}' branch has commits your branch has never seen. A Rebase is required before you can deliver.", file=sys.stderr)
            print(f"💡 Run: git rebase {self.get('remote')}/{self.get('default_branch')}")                  
            if self.get('is_dirty'):
                print("⚠️  Psst: Your workspace is dirty you must stash or commit your changes first)", file=sys.stderr)


        if not self.get('is_dirty'):
            print("☝️  Nothing to commit. The working directory is clean.")

            if self.get('sha1') != self.get('remote_sha1'):                
                print("👉 The branch is ahead of its remote; ...pushing")
                self._push(force=True)
            return None

        # If nothing is staged, stage all changes
        if not len(self.get('staged_changes')) > 0:
            # Stage all changes if nothing is staged
            asyncio.run(self._run('add_all'))
            self._load_status(reload=True)

        self.set('commit_msg',f"\"{message} - #{self.get('issue_number')}\"")

        asyncio.run(self._run('commit_changes') )
        self._push(force=True)

        issue_comments = Issue().load(number=self.get('issue_number')).get("comments")
        self.set('responsibles_comment_content', self._get_responsibles(issue_comments=issue_comments))

        responsibles_alert = ''
        if self.get('responsibles_comment_content'):
            asyncio.run(self._run("add_responsibles_comment"))

            responsibles_alert = f"\n☝️ You touched on files that have named responsibles {self.get('responsibles_comment_content')}\nThey are now mentioned in the issue."


        print(f"👍 SUCCESS: Branch has got a new commit that mentions issue '#{self.get('issue_number')}' and it's pushed\n{responsibles_alert}")
        print("💡 Run: gh workflow view wrapup")      
        print(f"💡 Run: gh browse {self.get('issue_number')}")
        return True
    
    def _get_responsibles(self, issue_comments: list[str]):
        change_list = self._get_pretty_changes()
        changed_past = self._past_responsible_file_paths(issue_comments=issue_comments)
        changed_new = set(change_list) - set(changed_past)

        return Responsibles().responsibles_as_markdown(
            changeset=changed_new,
            exclude=[f"@{self.get('me')}", *changed_new]
        )

    def _past_responsible_file_paths(self, issue_comments: list[dict]):
        """
        Returns:
            set: All file paths that responsibles have been previously notified about
        """

        comment_bodies = [comment["body"] for comment in issue_comments]

        file_paths = set()
        for body in comment_bodies:
            if body.startswith(Responsibles.responsibles_markdown_prefix()):
                matches = re.findall(r'`([^`]*)`', body)
                file_paths = file_paths.union(set(matches))
        return file_paths

    def _load_status(self, *, reload: bool = False):
        """Load the status of the current branch sets the following properties:
        - 'status': The output of `git status --porcelain`
        - 'is_dirty': True if there are unstaged or staged changes
        - 'unstaged_changes': List of unstaged changes
        - 'staged_changes': List of staged changes"""

        # Not in force reload mode
        if (not reload
            and self.get('is_dirty') is not None
            and self.get('unstaged_changes')
            and self.get('staged_changes')
        ):
            # If the status is already loaded, return
            return

        asyncio.run(self._assert_props(['status']))

        if reload:
            asyncio.run(self._force_prop_reload('status'))

        self.props['unstaged_changes'] = []
        self.props['staged_changes'] = []
        for line in self.get('status').splitlines():
            if line.startswith(('??', ' M', ' D')):
                self.props['unstaged_changes'].append(line)
            elif line.startswith(('M ', 'MM', 'A ', 'D ')):
                self.props['staged_changes'].append(line)
            else:
                # Don't ignore other lines, they might be useful
                self.props['unstaged_changes'].append(line)
        self.set('is_dirty',  len(self.props['unstaged_changes']) > 0 or len(
            self.props['staged_changes']) > 0)
        
    def _get_pretty_changes(self, *, staged: bool = True, unstaged: bool = False):
        """Get a pretty formatted list of changes
        
        Args:
            staged (bool): If True, include staged changes
            unstaged (bool): If True, include unstaged changes
        Returns:
            list: A list of changes with the tailing ' M', 'MM', 'A ' or '??' removed
        """
        asyncio.run(self._assert_props(['status']))
        self._load_status()
        changes = []
        if staged:
            changes.extend(self.get('staged_changes'))
        if unstaged:
            changes.extend(self.get('unstaged_changes'))

        ## Go through all items and remove the tailing ' M', 'MM', 'A ' or '??' 
        changes = [re.sub(r'^\s*([?M]+|A\s+)', '', change) for change in changes]
        # Remove leading whitespace
        return [change.lstrip() for change in changes]

    def set_issue(
            self,
            issue_number: int,
            label:str | None = None,
            msg:str | None = None,
            *, assign = True,
            reopen : bool = False
        ):
        """Set the issue number context to work on"""

        asyncio.run(self._assert_props(['remote', 'default_branch']))

        self.set('issue_number', issue_number)
        self.set('assign', assign)

        issue = Issue.load(number=issue_number)

        if issue.get('closed'): 
            if not reopen:
                print(f"⛔️ ERROR: Issue '{issue_number}' is closed, you must use --reopen if you want to work on this issue.", file=sys.stderr)
                sys.exit(1)
            # Reopen the issue if it is closed
            issue.reopen()

        reuse = asyncio.run(self.__reuse_issue_branch(issue_number=issue_number))
        if not reuse:
            # Construct a valid branch name based on the issue number, and the title, replacing spaces with underscores and weed out any chars that aren't allowind in branch names
            issue_title = issue.get('title')
            branch_valid_title = re.sub(
                '[^a-zA-Z0-9_-]', '', re.sub(' ', '_', issue_title))
            branch_name = f"{issue_number}-{branch_valid_title}"
            self.set('branch_name', branch_name)
            self.__develop()

        # at this point the branch should exist and is checked out - either through a local branch, a remote branch or a new branch

        # TODO Update the data used for metrics: 1) assignee, 2) add to project 3) update project field

        # assign the issue to the current user
        if self.get('assign'):
            issue.assign(assignee='@me')

        issue.label(label=label)


        if msg:
            # add the body to the issue
            issue.comment(msg=msg)

        # add the issue to the project and set the Status
        project = Project()
        workon_field = "Status"
        workon_field_value = project.get('workon_action')

        # TODO get the values from the config
        project.update_field(url=issue.get(
            'url'), field=workon_field, field_value=workon_field_value)

    def deliver(self):
        """Mapped to the 'deliver' subcommand."""

        asyncio.run(self._assert_props(['branch_name', 'remote']))

        self.__squeeze()
        ready_prefix = Config.config()['deliver']['policies']['branch_prefix']
        self.set('ready_prefix', ready_prefix)

        
        asyncio.run(self._load_issue_number())
        issue = Issue.load(number=self.get('issue_number'))
        project = Project()
        field = "Status"
        field_value = project.get('deliver_action')
        project.update_field(url=issue.get(
            'url'), field=field, field_value=field_value)

        asyncio.run(self._run('push_squeeze'))

        print(
            f"👍 SUCCESS: Branch '{self.get('branch_name')}' has been squeezed into one commit; '{self.get('squeeze_sha1')[:7]}' and pushed to {self.get('remote')} as '{ready_prefix}/{self.get('branch_name')}'")
        print("💡 Run: gh workflow view ready")

        return self.get('squeeze_sha1')

    def responsibles(self, exclude:str, *, unstaged: bool, staged: bool, ):

        asyncio.run(self._assert_props(['me']))

        exclude_list = []
        if exclude is not None:
            exclude_list = exclude.split(',')

        # replace @me with the current user
        exclude_list = [item.replace('@me', f"@{self.get('me')}") for item in exclude_list]

        asyncio.run(self._load_issue_number())
        self._load_status()
        change_list = self._get_pretty_changes(staged=staged, unstaged=unstaged)
        responsibles = Responsibles().responsibles_parse(
            changeset=change_list,
            exclude=exclude_list
        )

        if not responsibles:
            return
        # print each line of responsibles
        for item in responsibles:
            # Split the item into file path and responsibles
            file_path, responsibles = item.split(' (', 1)
            responsibles = responsibles.rstrip(')')
            # Format the item as a markdown list item
            print(f"{file_path} ({responsibles})")


    def get_sync(self, key: str):
        """Get a property value by key"""
        asyncio.run(self._assert_props([key]))
        return super().get(key)
