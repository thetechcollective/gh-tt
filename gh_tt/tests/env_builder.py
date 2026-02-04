"""
Integration test environment builder.

Provides a fluent API to declaratively build test environments with
GitHub resources (repos, issues) and local git clones.
"""

import contextlib
import json
import os
import tempfile
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from gh_tt import shell
from gh_tt.classes.config import CONFIG_FILE_NAME


class IntegrationEnv:
    """
    Builder and context for integration test environments.
    
    Use the fluent API to declare what resources you need, then call build()
    to create them. The same instance holds the created resources and handles cleanup.
    
    Assumes running in GitHub Actions context with GH_TOKEN and QA_ORGANIZATION_ID set.
    
    Usage:
        async with (IntegrationEnv()
            .require_owner()
            .create_repo()
            .create_issue()
            .create_local_clone()
            .build()) as env:
            
            # Access created resources
            assert env.issue_number is not None
            await shell.run(["some", "command"], cwd=env.local_repo)
    """
    
    def __init__(self):
        # Resource state (populated during build)
        self.owner: str | None = None
        self.repo_url: str | None = None
        self.local_repo: Path | None = None
        self.issue_number: int | None = None
        self.project_number: int | None = None
        
        # Build steps: list of (name, async_create_fn, async_cleanup_fn)
        self._steps: list[tuple[str, callable, callable]] = []
        
        # Track temp directory for cleanup
        self._temp_dir: tempfile.TemporaryDirectory | None = None
    
    def require_owner(self) -> Self:
        """
        Require a GitHub owner from QA_ORGANIZATION_ID environment variable.
        """
        async def create():
            qa_org_id = os.getenv("QA_ORGANIZATION_ID")
            assert qa_org_id is not None, "QA_ORGANIZATION_ID environment variable must be set"
            
            result = await shell.run([
                "gh", "api", "graphql",
                "-f", f'query=query {{ node(id: "{qa_org_id}") {{ ... on Organization {{ name }} }} }}'
            ])
            self.owner = json.loads(result.stdout)['data']['node']['name']
        
        async def noop():
            pass
        
        self._steps.append(("owner", create, noop))
        return self
    
    def create_repo(self) -> Self:
        """Create a private GitHub repository."""
        async def create():
            assert self.owner, "Owner required before creating repo (call require_owner first)"
            repo_name = f"{self.owner}/{self._generate_name('repo')}"
            result = await shell.run([
                "gh", "repo", "create", repo_name, "--private"
            ])
            self.repo_url = result.stdout
        
        async def cleanup():
            if self.repo_url:
                await shell.run([
                    "gh", "repo", "delete", self.repo_url, "--yes"
                ], die_on_error=False)
        
        self._steps.append(("repo", create, cleanup))
        return self
    
    def create_issue(self, title: str | None = None) -> Self:
        """Create an issue in the repository."""
        async def create():
            assert self.repo_url, "Repo required before creating issue"
            issue_title = title or uuid.uuid4().hex[:8]
            result = await shell.run([
                "gh", "issue", "create",
                "-R", self.repo_url,
                "--title", issue_title,
                "--body", ""
            ])
            # Result is issue URL like https://github.com/owner/repo/issues/1
            self.issue_number = int(result.stdout.split("/")[-1])
        
        async def noop():
            pass
        
        self._steps.append(("issue", create, noop))
        return self
    
    def create_local_clone(self, default_branch: str = "main") -> Self:
        """
        Create a local git repository.
        
        If a remote repo exists, connects to it as origin.
        """
        async def create():
            self._temp_dir = tempfile.TemporaryDirectory()
            self.local_repo = Path(self._temp_dir.name)
            
            # Initialize git repo
            for cmd in [
                ["git", "init"],
                ["git", "checkout", "-b", default_branch],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Integration Test"],
                ["git", "config", "push.autoSetupRemote", "true"],
                ["git", "commit", "--allow-empty", "-m", "Initial commit"],
            ]:
                await shell.run(cmd, cwd=self.local_repo)
            
            if self.repo_url:
                await shell.run(
                    ["git", "remote", "add", "origin", self.repo_url],
                    cwd=self.local_repo
                )

                # Push initial commit so remote has a default branch
                await shell.run(
                    ["git", "push", "-u", "origin", default_branch],
                    cwd=self.local_repo
                )
        
        async def cleanup():
            if self._temp_dir:
                self._temp_dir.cleanup()
        
        self._steps.append(("local_clone", create, cleanup))
        return self
    
    def create_gh_project(self) -> Self:
        async def create():
            assert self.owner, "Owner required before creating a project (call require_owner first)"

            project_title = self._generate_name('project')
            project_number = await shell.run(['gh', 'project', 'create', '--title', project_title, '--owner', self.owner, '--format', 'json', '--jq', '.number'])
            self.project_number = project_number

        async def cleanup():
            await shell.run(['gh', 'project', 'delete', self.project_number, '--owner', self.owner], die_on_error=False)
            
        self._steps.append(('project', create, cleanup))
        return self

    def add_project_config(self, workon_status_value: str) -> Self:

        async def create():
            assert self.local_repo is not None, 'Local repo required before adding config'
            assert self.project_number, 'Project required before adding config'
            assert self.owner, "Owner required before creating a project (call require_owner first)"
            with Path.open(self.local_repo / CONFIG_FILE_NAME, 'w') as f:
                f.write(json.dumps({
                    'workon': {
                        'status': workon_status_value
                    },
                    'project': {
                        'owner': self.owner,
                        'number': self.project_number
                    }
                }))

        async def noop():
            # Is removed together with the local repo temp directory
            pass

        self._steps.append(('project_config', create, noop))
        return self
    
    @contextlib.asynccontextmanager
    async def build(self) -> AsyncIterator[Self]:
        """Build the environment and yield self, then clean up."""
        pending_cleanups = []
        
        try:
            for name, create_fn, cleanup_fn in self._steps:
                await create_fn()
                pending_cleanups.append((name, cleanup_fn))
            yield self
        finally:
            for name, cleanup_fn in reversed(pending_cleanups):
                try:
                    await cleanup_fn()
                except Exception as e:
                    print(f"Warning: cleanup of {name} failed: {e}")
    
    @staticmethod
    def _generate_name(infix: str = "") -> str:
        """Returns a timestamped name for naming autogenerated resources."""
        today_iso = datetime.now(UTC).date().isoformat()
        return f"gh-tt-test-{infix}-{today_iso}-{uuid.uuid4().hex[:8]}"