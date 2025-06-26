# gh-tt
This utility supports the workflow used by the _.tech that_ full-stack team within [_.the tech collective_](https://thetechcollective.eu/). It is designed as an [opinionated flow](docs/workflow.md). If you share our values and like our process, you can easily set this up for your own team.

**Addendum**
 - [The opinionated .tech that workflow](docs/workflow.md)
 - [How we work with _mentorship_ over _pull requests_](docs/responsibles.md)

## Introduction
In short, `gh-tt` supports a workflow that
1. follows trunk-based development practices (`main` is the only long-lived branch)
2. does **not** rely on Pull Requests
3. works with [RESPONSIBLES](docs/responsibles.md) (CODEOWNERS reimplemented for the PR-less team)

`gh tt` implements ideas from DevOps, GitOps and CI/CD, wrapped up into a sweet, deeply configurable, workflow. It looks something like this:
1. `gh tt workon -i 101` - start working on issue #101
    - Create a new development branch and switch to it
    - Move the issue to `In Progress` in a GitHub Project
2. Hackity hack clickity clack
3. `git add .`
4. `gh tt wrapup -m "Rewrite everything in Rust"`
    - Create and push a new commit to the development branch, automatically mentioning the issue
    - Parse and notify `RESPONSIBLES`
    - Run CI
6. `gh tt deliver`
    - Squash the development branch into one commit, create and push a new `ready/<dev_branch_name>` branch with that commit
    - Run CI
    - If CI passes, fast-forward merge the ready branch commit to main

Read about it in more detail in [docs/workflow.md](docs/workflow.md).
See it in action in this repository, e.g. [#206](https://github.com/thetechcollective/gh-tt/issues/206).

## Feedback, discussions, contributing
Issues are open on the repo: [`thetechcollective/gh-tt`](https://github.com/thetechcollective/gh-tt/issues). If you experience errors, misbehavior, or have feature requests, feel free to join the discussion.

For contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Getting started

### Install

This utility is a GitHub Command Line extension.

Dependencies:

- `python3` – any version, but developed and tested on v3.13. No additional Python dependencies ([install Python](https://www.python.org/downloads/))
- `gh` – the GitHub Command Line Interface ([install GitHub CLI](https://github.com/cli/cli#installation))

Once you have both dependencies installed, run:

```sh
gh extension install thetechcollective/gh-tt
```

The extension requires write access to GitHub Projects (scope `project`). If you don't have it, you'll be prompted with instructions.

### Configure required values
Create a `tt-config.json` in the root of your repository. You can take inspiration from the default configuration file, [classes/tt-config.json](classes/tt-config.json).

> [!IMPORTANT]
> `gh tt` requires a GitHub Project to work with.

The minimal required configuration looks like:

```json
{
    "project": {
        "owner": "thetechcollective",
        "number": 1
    }
}
```

### Configure optional values
You might also want to configure which `Status` issues are assigned when executing `workon` (start working on an issue) and `deliver` (finish and push to `main` if CI passses).

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

## Syntax

Run `gh tt -h` to see the syntax.

The extension provides four subcommands: `workon`, `wrapup`, and `deliver`, `responsibles`. See the [workflow](docs/workflow.md) for details.

> [!TIP]
> Each subcommand supports the `-h, --help` option to display in-detail guidance for the specific subcommand, e.g.
> `gh tt workon -h`

For an overview, run `gh tt -h`
```sh
usage: gh tt [-h] [-v] [--version] {workon,wrapup,deliver,responsibles,semver} ...

A command-line tool to support a consistent team workflow. It supports a number of subcommands which
define the entire process: `workon`, `wrapup`, `deliver`. Use the `-h|--help` switch on each to learn
more. The extension utilizes the GitHub CLI tool `gh` to interact with GitHub and therefore it's
provided as a gh extension. GitHub Projects integration is supported. It enables issues to
automatically propagate through the columns in the (kanban) board. Please consult the README.md file
in 'thetechcollective/gh-tt' for more information on how to enable this feature - and many more neat
tricks.

positional arguments:
  {workon,wrapup,deliver,responsibles,semver}
    workon              Set the issue number context to work on
    wrapup              Commit the status of the current issue branch and push it to the remote
    deliver             Create a collapsed 'ready' branch for the current issue branch and push it to
                        the remote
    responsibles        List the responsibles for the current issue branch
    semver              Reads and sets the current version of the repo in semantic versioning format

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output
  --version             Print version information and exit
```

## Workflow nice-to-haves
Next to `gh-tt`, we also use devcontainers. Here's some neat tricks that will make your life easier.

For inspiration, see [`devcontainer.json`](.devcontainer/devcontainer.json) in this repo.

```json
"initializeCommand": "./.devcontainer/initializeCommand.sh",
"postCreateCommand": "./.devcontainer/postCreateCommand.sh",
```

Both are designed as one-liners and are placed in separate files.

[**`initializeCommand.sh`**](.devcontainer/initializeCommand.sh)

Uses [`gh-login.sh`](.devcontainer/gh-login.sh) to generate a token from your host machine and prepare it for reuse in the container by [`postCreateCommand.sh`](.devcontainer/postCreateCommand.sh). This allows your container to inherit your host's `gh auth` status.

[**`postCreateCommand.sh`**](.devcontainer/postCreateCommand.sh)

Expands the repo's `.git/.gitconfig` with some additional aliases defined in [`.gitconfig`](.gitconfig). Git does not natively support a `.gitconfig` file in the repository root. So we add it:
https://github.com/thetechcollective/gh-tt/blob/47ec72e23a2aa7c9d3879989586a1655c4362911/.devcontainer/postCreateCommand.sh#L11-L12

We install the GitHub extension:
https://github.com/thetechcollective/gh-tt/blob/47ec72e23a2aa7c9d3879989586a1655c4362911/.devcontainer/postCreateCommand.sh#L25

And import some aliases
https://github.com/thetechcollective/gh-tt/blob/47ec72e23a2aa7c9d3879989586a1655c4362911/.devcontainer/postCreateCommand.sh#L27

This creates shortcuts so you can run:

```sh
gh workon        # instead of gh tt workon
gh wrapup        # instead of gh tt wrapup
gh deliver       # instead of gh tt deliver
gh responsibles  # instead of gh tt responsibles
```
