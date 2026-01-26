# 2026-01-23 Workflow update

The team noticed that we use gh-tt to various extent with various success. We discussed what changes in the workflow we want and how the `gh-tt` can support those needs. The results of that meeting are captured below.

## Status quo
There were three main requirements that landed us on the current workflow:
- we must fast-forward into `main`
- issues and PRs are poor conceptually - all work should be tracked on the issue
- PRs imply a blocking review state

The points all well expanded on here - https://www.lakruzz.com/stories/githubs-enfant-terrible/#so-whats-the-problem---in-github

### Fast-forwarding into `main`

In favor of simplifying our workflow and its implementation in the tool, we are letting go of this requirement. We recognize its a best practice in configuration management and a hard-requirement in regulated industries.

Nevertheless, we are going YAGNI on this one, and will reimplement fast-forwarding when we burn ourselves, or are required to do it.

### PRs vs. issues

Although having the work log in one place (ideally the issue), the split between issues and PRs does not worry us that much. We will retain all 'code-work' history in the PR, and the issue might be a somewhat sad, somewhat empty container. **Generally, issues are to describe the problem and PRs should describe the solution.**

We like the affordances of PRs - native status checks, better diff comparison, coding agent reviews, easier collaboration with external developers, ...

Communication about business logic should be as close to the client as possible (ADO or whatever platform the client is using), comms about the implementation should be in the PR.

### PRs imply a blocking review

Blocking reviews are a completely self-imposed step in the process. PRs might make reviews the default, but are in no way required. We are keeping our philosophy of non-blocking entry to `main`. No changes are expected due to using PRs.

## Going forward
[View the repository before these changes were implemented](https://github.com/thetechcollective/gh-tt/tree/f96c697d31436d393dd58375ef4b408016709f69)

Given these considerations, we have identified the following adjustments to `gh-tt`:

- `workon`
  - should create a draft PR which in connected to the issue
  - creating an issue is still required
- `wrapup`
  - to be removed, devs are free to use whatever way they feel appropriate to contribute to their branches
- `deliver`
  - checks for a PR
  - gives option to auto-merge
- `responsibles`
  - right now broken
  - agreed that we still need a (non)blocking way to be notified about changes in parts of the codebase we self-select into
- `semver`
  - not discussed, keeping as-is