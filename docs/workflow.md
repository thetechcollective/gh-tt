# .tech Workflow

## Suitability Filter

This workflow is opinionated and tailored for teams who value a streamlined, GitHub-centric process. If you share our approach, this workflow will suit you well.

👉 **GitHub-Centric:** We use GitHub _repositories_, _issues_, _projects_, and _actions_ as the backbone of our workflow.<br/>
👉 **Kanban Approach:** Our kanban board is implemented using GitHub _issues_ and a single _project_ that serves as both our upstream and downstream board.<br/>
👉 **Single Long-Lived Branch:** We maintain only one long-lived branch, `main`. All other branches are short-lived and intended to be closed as soon as possible.<br/>
👉 **Issue-Driven Development:** Every addition—be it development, bug-fixing, or refactoring—starts with a GitHub _issue_. No commits are allowed on `main` unless they are linked to an issue.<br/>
👉 **Pristine Main:** The `main` branch is always _shippable_ and _pristine_. Only commits that pass the `pre-deliver` quality gate are allowed, and only fast-forward merges are permitted.<br/>
👉 **Squashed Commits:** All commits on development branches are squashed into a single commit, which is then pushed as a _ready_ branch (`ready/**`).<br/>
👉 **Five-Tier Automated Testing:**  
1. Issue branches (`[0-9]-**`) trigger a `pre-deliver` workflow for internal status checks.
2. `ready/**` branches trigger a `ready` workflow. If all checks pass, the branch is automatically merged to `main`.
3. Commits on `main` are deployed to the `dev` environment and tested. Passing commits are labeled as _release candidates_ (`<major>.<minor>.<sequence>rc`).
4. Release candidates are deployed to `qa` (stage) and tested. Passing commits are marked as _shippable_.
5. When ready for production, the latest _shippable_ commit is labeled (`<major>.<minor>.<patch>`) and deployed to `prod`.<br/>

👉 **Mentorship Over Pull Requests:** Instead of pull requests, we use a [`RESPONSIBLES`](responsibles.md) file (similar to `CODEOWNERS`). If a commit affects files with assigned responsibles, those individuals are mentioned on the issue to review or assist. This trust-based mentorship model replaces traditional quality gates.

The `gh` extension `thetechcollective/gh-tt` is designed to support this workflow, with three core subcommands: `workon`, `wrapup`, and `deliver`, which manage the branching strategy.

Additional supporting tools include:

- [`thetechcollective/gh-rotator`](/thetechcollective/gh-rotator): Orchestrates individually releasable components (repos) into a composite product that rotates automatically when any part is updated.
- [`thetechcollective/gh-downstream`](/thetechcollective/gh-downstream): Reports lead times in our kanban board.
- [`lakruzz/semver`](/lakruzz/gh-semver): Bumps semantic version labels for both release candidates and production releases.

---

## Workon, Wrapup, Deliver

This is the core development cycle. Each increment to `main` follows this process:

### Workon

**Checks out a branch for an issue. If a branch already exists (locally or remotely), it reuses it; otherwise, it creates a new branch. The issue is assigned to you. If a GitHub project is connected, the issue is added to the project and its status is set to `Work in Progress`.**

```sh
gh tt workon -i 23
```

Typically, you start with an issue in the _To Do_ column of the downstream board. The context is always the current repository—cross-repo work requires checking out the other repo.

To create and immediately work on a new issue:

```sh
gh tt workon -t "Correcting some spelling"
```

This is syntactic sugar for:

```sh
issue_number=$(gh issue create -t "Correcting some spelling" -b "" | grep -oE '[0-9]+$')
gh tt workon -i "$issue_number"
```

All `gh tt` commands support `--verbose` for detailed output and `--help` for usage information:


---

## Wrapup

**Stages your changes (if not already staged), creates a commit with your message and a reference to the issue, and checks the `RESPONSIBLES` file for any additional reviewers. If responsibles are found, it comments on the issue and mentions them. Finally, it pushes the branch, triggering the `pre-deliver` workflow.**

```sh
gh tt wrapup -m "Finished a subset of the issue, taking a break"
```

Reasons to use `wrapup`:

- To safely push your current work before a break.
- To celebrate a milestone.
- To notify a responsible when touching unfamiliar files.
- To request help from a colleague.
- To leverage detailed insights from the `pre-deliver` workflow.

There are no strict rules on the issue branch—work as you see fit. Use `--verbose` to see detailed operations.

---

## Deliver

**Requires your development branch to be rebased onto `main`. Squashes all commits on your issue branch into a single commit, using the issue title as the commit message header and listing all individual commit messages. Pushes this as a `ready/**` branch, triggering the `ready` workflow. If all checks pass, the branch is fast-forward merged to `main`, and both the issue and ready branches are deleted. The issue is then closed.**

```sh
gh tt deliver
```

If the `ready/**` branch fails checks, simply continue working on the issue branch, use `wrapup` as needed, and rerun `deliver` when ready.
