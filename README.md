<!-- cspell:ignore Hackity, clickity -->
# gh-tt
This utility supports the workflow used by the _.tech that_ full-stack team within [_.the tech collective_](https://thetechcollective.eu/). If you are considering working with us - this is your chance to get a feel for our continuous integration process.

## Introduction
In short, `gh-tt` supports a workflow that
- follows trunk-based development practices (`main` is the only long-lived branch)
- does **not** use Pull Requests for peer-reviews, wait states and bureaucracy

`gh tt` implements ideas from DevOps, GitOps and CI/CD, wrapped up into a sweet, configurable, workflow. It looks something like this:
1. `gh tt workon -i 101` - start working on issue #101
    - Create a new development branch and switch to it
    - Create a PR on GitHub
    - Move the issue to `In Progress` in a GitHub Project
2. Hackity hack clickity clack
3. `git add .`
4. `git commit -m 'Rewrite everything in Rust'`
6. `gh tt deliver`
    - Enable auto-merge on the PR (merges the PR when the CI pipeline is green)

## Getting started

### Install

This utility is a GitHub Command Line extension.

Dependencies:

- `python3` – version 3.11+
- `gh` – version 2.55+, the GitHub Command Line Interface ([install GitHub CLI](https://github.com/cli/cli#installation))

Once you have both dependencies installed, run:

```sh
gh extension install thetechcollective/gh-tt
```

The extension requires write access to GitHub Projects (scope `project`). If you don't have it, you'll be prompted with instructions.

### Configuration
Configuration is possible via `.tt-config.json` in the root of your repository. You can take inspiration from the default configuration file, [classes/tt-config.json](classes/tt-config.json).

To add issues you work on to a GitHub Project:
```jsonc
{
    "project": {
        "owner": "your-github-organization",
        "number": 1 # The project number
    }
}
```

You might also want to configure which `Status` issues are assigned when executing `workon` (start working on an issue) and `deliver` (PR auto-merge enabled).

The defaults are
```json
{
    "workon": {
        "status": "In Progress"
    },
    "deliver": {
        "status": "Delivery Initiated"
    }
}
```

> [!TIP]
> There's many more configuration options laid out in [`classes/tt-config.json`](classes/tt-config.json). 


### Add files to `.gitignore`

Our setup may pollute the workspace with two files you might want to add to `.gitignore`:

```gitignore
.tt_cache
_temp.token
```

- `.tt_cache` is used to optimize execution. If you change project settings in `.tt-config.json`, delete this cache.
- `_temp.token` is related to the optional configuration described below. It's created and used by `gh-login.sh`. You only need to add it to `.gitignore` if you use `gh-login.sh`.

## Usage

Run `gh tt -h` to see the syntax.

The extension supports four subcommands: `workon`, `deliver`, and `semver`. See the [workflow](docs/workflow.md) for details. Each subcommand supports the `-h, --help` option to display in-detail guidance for the specific subcommand, e.g. `gh tt workon -h`.

Commands `wrapup`, `status` and `sync` are deprecated and will be removed in the future.

> [!WARNING]
> The extension is migrating to a PR-flavored workflow. Run this by passing the --pr-workflow flag to `workon` or `deliver`.

For an overview, run `gh tt -h`
```sh
usage: gh tt [-h] [-v] [--pr-workflow] [--version] {workon,wrapup,deliver,semver,status,sync} ...

A command-line tool to support a consistent team workflow. It supports a number of subcommands which define the entire
process: `workon`, `wrapup`, `deliver`. Use the `-h|--help` switch on each to learn more. The extension utilizes the GitHub
CLI tool `gh` to interact with GitHub and therefore it's provided as a gh extension. GitHub Projects integration is supported.
It enables issues to automatically propagate through the columns in the (kanban) board. Please consult the README.md file in
'thetechcollective/gh-tt' for more information on how to enable this feature - and many more neat tricks.

positional arguments:
  {workon,wrapup,deliver,semver,status,sync}
    workon              Set the issue number context to work on
    wrapup              Commit the status of the current issue branch and push it to the remote
    deliver             Create a collapsed 'ready' branch for the current issue branch and push it to the remote
    semver              Reads and sets the current version of the repo in semantic versioning format
    status              Set or get the status of a commit
    sync                Sync GitHub items from a template repository to all sibling repositories

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output. -v for INFO, -vv for DEBUG
  --pr-workflow         Migration flag to ease transition to a new workflow
  --version             Print version information and exit
```
