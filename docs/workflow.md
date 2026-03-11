# `gh tt` workflow in detail

- **GitHub-Centric:** We use GitHub _repositories_, _issues_, _projects_, and _actions_ as the backbone of our workflow
- **Kanban Approach:** Our kanban board is implemented using GitHub _issues_ and a single _project_ that serves as both our upstream and downstream board
- **Single Long-Lived Branch:** We maintain only one long-lived branch, `main`; all other branches are short-lived and intended to be closed as soon as possible
- **Issue-Driven Development:** Every addition — be it development, bug-fixing, or refactoring—starts with a GitHub _issue_; no commits are allowed on `main` unless they are linked to an issue
- **Pristine Main:** The `main` branch is always _shippable_ and _pristine_; only commits that pass the `CI` quality gate are allowed
- **Squashed Commits:** All commits on development branches are squashed into a single commit

The `gh` extension `thetechcollective/gh-tt` is designed to support this workflow, with two core subcommands: `workon`, and `deliver`, which manage the branching strategy.

Additional supporting tools include [`thetechcollective/gh-rotator`](/thetechcollective/gh-rotator): Orchestrates individually releasable components (repos) into a composite product that rotates automatically when any part is updated.

---

## workon, add, commit, deliver

This is the core development cycle. Each increment to `main` follows this process:

### gh tt workon

**Checks out a branch for an issue. If a branch already exists (locally or remotely), it reuses it; otherwise, it creates a new branch. The issue is assigned to you. If a GitHub Project is connected, the issue is added to the project and its status is set to `In Progress`.**

```sh
gh tt workon -i 23
```

To create a new issue and immediately start working on it:

```sh
gh tt workon -t "Correcting some spelling"
```


## add, commit, push
Work on your branch in any manner that you see fit! For most folks, that will be something to the extent of:
```sh
# change some files
git add .
git commit -m 'Rewrite everything in Rust'
git push
# repeat
```

## gh tt deliver
Enables auto-merge on the PR connected to your issue.

```sh
gh tt deliver
```
