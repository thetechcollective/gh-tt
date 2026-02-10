# Migration guide

This guide describes the changes to be made to projects in order to migrate to the new PR-flavored workflow.

## GitHub Merge Queues

The new workflow does not strictly require the use of GitHub Merge Queues, but it is **recommended**. As such, this guide walks through implementing a queue.

Merge queues are an implementation of the 'Not Rocket Science' principle built right into GitHub.

> [The Not Rocket Science Rule Of Software Engineering](https://graydon2.dreamwidth.org/1597.html):
> 
> automatically maintain a repository of code that always passes all the tests

Imagine the following scenario (which was impossible in the previous version of `gh-tt` due to the workings of `wrapup` and `deliver`):
- We have two PRs ready to merge to `main`, both passing the tests on their respecting branches
- In PR 1, function `foo()` is called in a new piece of functionality
- In PR 2, function `foo()` is renamed and all call sites are updated
- If both PRs are merged without a rebase between them, `main` will be broken

A merge queue prevents this situation. It creates a new branch where it tests the new changes integrated on top of `main`. If the changes do not pass tests, they are not merged.

If this sounds a lot like the old `deliver` and `ready` branch mechanism, thats because it is! Except this one is built into GitHub and does not have the problem of having to rebase all changes and pass tests before you can merge.


## Configuration

### GitHub Actions

The new process requires one GH workflow that is run on push and merge queue. It's going to look something like:

```yaml
name: Quality gates

on:
  workflow_dispatch:
  merge_group:
  push:
    branches: 
      - '[0-9]*'
```

Then you can run your quality checks. E.g. running tests in a Python repo with `uv`:

```yaml
e2e:
    name: End to end tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          # Latest python compliant with the project's requires-python
          python-version-file: 'pyproject.toml'

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
            # Latest uv compliant with the project's tool.uv required version
            version-file: 'pyproject.toml'
      - name: Run pytest
        run: |
          uv run pytest
```

For simpler management of checks that are required to merge, also set up this 'godfather' of all checks:

```yaml
check:  # This job does nothing and is only used for the branch protection
    name: ✅ All passed
    if: always()

    needs:
    - ruff_linting
    - ruff_formatting
    - pytest_with_coverage

    runs-on: ubuntu-latest

    timeout-minutes: 1

    steps:
    - name: Decide whether the needed jobs succeeded or failed
      uses: re-actors/alls-green@05ac9388f0aebcb5727afa17fcccfecd6f8ec5fe # v1.2.2
      with:
        jobs: ${{ toJSON(needs) }}
```

This check will only pass if all checks in the `needs:` list pass (it has more [configuration](https://github.com/re-actors/alls-green/tree/unstable/v1) options).

Then in [repository settings](#repository-settings), you can choose this one check instead of choosing one-by-one. This is especially annoying as there is no option of 'require **all** checks to pass'.


In conclusions, todos here are
- [ ] Rename `wrapup.yaml` to e.g. `quality_gate.yaml` or `push.yaml`
- [ ] Add the `merge_group` workflow trigger
- [ ] Add the 'All passed' job
- [ ] Remove `ready.yaml`


### Repository settings

In the repo settings (Settings -> General), configure the following:
- Features
    - [x] Issues
- Pull Requests
    - [x] Allow squash merging
    - [x] Allow auto-merge
    - [x] Automatically delete head branches
- Issues
    - [x] Auto-close issues with merged linked pull requests

#### Branch protection

Add a [branch ruleset](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) on the default (main) branch.

Configure the following
- [x] Restrict deletions
- [x] Require linear history
- [x] Require merge queue
    - Merge method: squash and merge
    - (In other fields you can leave defaults or adjust as necessary according to the [merge queue docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue))
    - [x] Require all entries to pass required checks
    - Status check timeout
        - This should be set to a value not much larger than the length of your verification GitHub action (e.g. if your quality gate takes 3mins, set to 3min 30sec)
- Require a pull request before merging
    - (Required approvals: 0 and no checks - we do not introduce blocking reviews by default)
    - Allowed merge methods: Squash
- [x] Require status checks to pass
    - + Add checks: 'All passed' (status check configured in [GitHub Actions](#github-actions))
- [x] Block force pushes

### GH CLI Aliases

In most projects, the `postCreateCommand.sh` adds some aliases, so you don't have to type out `tt` all the time.

If you'd like to _not_ type `--pr-workflow` all the time, you can change your aliases to add this flag.

```diff
- workon:  '!gh tt workon "$@"'
+ workon:  '!gh tt workon --pr-workflow "$@"'
wrapup:  '!gh tt wrapup "$@"'
- deliver: '!gh tt deliver "$@"'
+ deliver: '!gh tt deliver --pr-workflow "$@"'
responsibles: '!gh tt responsibles "$@"'
semver: '!gh tt semver "$@"'
```

### Need help?
1. Check out how the [`gh-tt` repo](https://github.com/thetechcollective/gh-tt) is set up as a reference implementation
2. Reach out to @vemolista


