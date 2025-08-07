import asyncio
import contextlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from operator import itemgetter

from gh_tt.classes.devbranch import Devbranch
from gh_tt.classes.gitter import Gitter
from gh_tt.classes.lazyload import Lazyload

# Helper functions 


def _check_pending_workflows(sha: str):
    """Check if there are any pending workflow runs for the given commit SHA
    Args:
        sha: The commit SHA to check for pending workflows (required)
    Returns:
        bool: True if there are pending workflows, False otherwise  
    """
    try:
        [result, _] = asyncio.run(Gitter(
            cmd=f"gh run list --commit {sha} --json status,conclusion,createdAt,name,workflowName",
            msg=f"Checking workflow runs for commit {sha[:8]}"
        ).run())
        
        if not result.strip():
            return False  # No workflows found
            
        workflows = json.loads(result)
        
        # Check if any workflows are still pending/queued/in_progress
        for workflow in workflows:
            status = workflow.get('status', '')
            if status in ['queued', 'in_progress', 'waiting', 'pending']:
                return True
                
        return False
        
    except Exception:
        # If we can't check workflows, assume no pending ones
        return False


def _get_icon(state: str) -> str:
    """Get the appropriate icon for a given status state"""
    icons = {
        'success': "✅",
        'failure': "❌", 
        'error': "💥",
        'pending': "⏳"
    }
    return icons.get(state, "❓")


def _process_statuses(statuses: list) -> tuple[bool, bool, int]:
    """Process status list, print status and return completion state
    
    Args:
        statuses: List of status objects from GitHub API
        
    Returns:
        tuple: (all_complete, all_success, lines_printed)
    """
    all_complete = True
    all_success = True
    lines_printed = 0

    with contextlib.suppress(KeyError):
        # When missing the sort key, just skip the sorting
        statuses = sorted(statuses, key=itemgetter('context'))

    for status in statuses:
        context = status.get('context', 'unknown')
        state = status.get('state', 'unknown')
        
        if state in ['pending']:
            all_complete = False
        elif state not in ['success']:
            all_success = False
        
        # Get appropriate icon for this state
        icon = _get_icon(state)
        
        print(f"   {icon} {context}: [{state}]{' ' * 40}")
        lines_printed += 1
    
    return all_complete, all_success, lines_printed


def _handle_exit_conditions(*, all_complete: bool, all_success: bool, has_pending_workflows: bool, has_patience: bool) -> int:
    """Handle exit conditions and print status message
    
    Args:
        all_complete: Whether all statuses are complete (not pending)
        all_success: Whether all statuses succeeded
        has_pending_workflows: Whether there are pending workflows
        has_patience: Whether we still have patience to wait for GitHub to register statuses
        
    Returns:
        int: Lines printed (1 for the final message), or -1 to continue polling
    """
    # Check if all statuses are complete (not pending) AND no workflows are pending
    if all_complete and not has_pending_workflows:
        # If we have patience and no statuses/workflows, wait for GitHub to register them
        if has_patience:
            print(f"⏳ Waiting for the commit to arrive at GitHub...{' ' * 15}")
            return 1  # Printed 1 line, continue polling
        
        if all_success:
            print(f"All checks passed! {' ' * 40}")
            sys.exit(0)
        else:
            print(f"Some checks failed! {' ' * 40}")
            sys.exit(1)
    else:
        if has_pending_workflows:
            print(f"⏳ Waiting for workflow runs to complete...{' ' * 15}")
        else:
            print(f"⏳ Waiting for status checks to complete...{' ' * 15}")
        return 1  # Printed 1 line
    
    return -1  # Should not reach here


def _handle_no_statuses(*, has_pending_workflows: bool, short_sha: str, interval: int, has_patience: bool) -> int:
    """Handle the case when no statuses are found
    
    Args:
        has_pending_workflows: Whether there are pending workflows
        short_sha: Short commit SHA for display
        interval: Polling interval in seconds
        has_patience: Whether we still have patience to wait for GitHub to register statuses
        
    Returns:
        int: Lines printed, or exits the program
    """
    if has_pending_workflows:
        print(f"Waiting for workflow runs to start for commit {short_sha}{' ' * 40}")
        time.sleep(interval)
        return 1  # Printed 1 line, continue polling
    
    # If we have patience and no statuses/workflows, wait for GitHub to register them
    if has_patience:
        print(f"⏳ Waiting for the commit to arrive at GitHub...{' ' * 15}")
        time.sleep(interval)
        return 1  # Printed 1 line, continue polling
    
    # No statuses and no pending workflows and no patience left - let's get out!
    print(f"No statuses found for commit {short_sha}{' ' * 40}")
    print(f"No workflows are pending - nothing to wait for{' ' * 40}")
    sys.exit(1)


class Status(Lazyload):
    """Class used to represent a GitHub commit status"""
   
    
    @classmethod
    def fetch_status(cls, sha: str | None = None, repository: str | None = None):
        """Fetch the status of a commit as json
        
        Args:
            sha: The SHA of the commit to get status for (optional, defaults to current HEAD)
            
        Returns:
            dict: Status information from GitHub API, None if error
        """

        # Get commit SHA
        if not sha:
            sha = os.getenv('GITHUB_SHA') # Get from environment variable in GitHub Actions context
            if not sha:
                sha = Devbranch().get_sync("sha1")

        # Get repository information
        if not repository:
            repository = os.getenv('GITHUB_REPOSITORY') # Get from environment variable in GitHub Actions context
            if not repository:
                repository = Devbranch().get_sync("repository")
        
        
        try:
            # Get the commit status from GitHub API
            cmd = f"gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' /repos/{repository}/commits/{sha}/status"
            
            [result, process] = asyncio.run(
                Gitter(
                    cmd=cmd,
                    msg=f"Getting commit status for SHA {sha[:8]}"
               ).run()
            )
            # Parse and return JSON result
            return json.loads(result)
            
        except Exception as e:
            print(f"ERROR: Failed to get commit status: {e}", file=sys.stderr)
            return None

    @classmethod
    def poll(cls, sha: str | None = None, repository: str | None = None, interval: int = 4, patience: int = 4):
        """Poll commit statuses until all are either success or failure (not pending)
        
        Args:
            sha: The SHA of the commit to poll status for (optional, defaults to current HEAD)
            repository: The repository to poll (optional, defaults to current repo)
            interval: Polling interval in seconds (default: 4)
            
        Returns:
            bool: True if all statuses succeeded, False if any failed
        """

        devbranch = Devbranch()
        # A sha and a repository is required - get'em none are given as arguments
        if not sha:
            sha = devbranch.get_sync("sha1") # Get from Devbranch (HEAD)
        short_sha = sha[:8] if sha else "unknown"

        # Get repository information
        if not repository:
            repository = devbranch.get_sync("repository")
        
        print("Press Ctrl+C to stop polling - will exit when all checks are done.")
        print(f"Polling commit {short_sha} for statuses every {interval} seconds...")
        
        # Start by assuming there might be pending workflows - The while loop will re-read this value if it's True, so no worries
        has_pending_workflows = True
        
        # Reserve space for dynamic status display - Start with 0 - couting will be done dynamically as we print
        reserved_lines = 0 
        
        # Loop counter for patience mechanism
        loop_count = 0
        
        try:
            while True:
                loop_count += 1
                has_patience = loop_count <= patience
                
                # Fetch current status data
                status_data = cls.fetch_status(sha, repository)
            
                
                statuses = status_data.get('statuses', [])
                
                # Only re-check pending workflows if we had them initially and still might have them
                if has_pending_workflows:
                    has_pending_workflows = _check_pending_workflows(sha)
                
                # Clear previous output BEFORE calculating new line count
                if reserved_lines > 0:
                    print(f"\033[{reserved_lines}A", end="")
                
                # First line: timestamp (always display this first)
                current_time = datetime.now(tz=UTC).strftime('%H:%M:%S')
                print(f"Last check {current_time}{' ' * 50}")
                reserved_lines = 1  # We just printed the timestamp line
                
                if not statuses:
                    extra_lines = _handle_no_statuses(
                        has_pending_workflows=has_pending_workflows, 
                        short_sha=short_sha, 
                        interval=interval,
                        has_patience=has_patience
                    )
                    reserved_lines += extra_lines
                    continue  
                
                # We have statuses to process
                all_complete, all_success, status_lines = _process_statuses(statuses)
                reserved_lines += status_lines  # Add the status lines
                
                # Handle exit conditions and final messaging
                final_lines = _handle_exit_conditions(
                    all_complete=all_complete, 
                    all_success=all_success, 
                    has_pending_workflows=has_pending_workflows,
                    has_patience=has_patience
                )
                reserved_lines += final_lines  # Add the final message line
                
                # reserved_lines now contains the exact number of lines we printed
                    
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nPolling interrupted by user")
    

