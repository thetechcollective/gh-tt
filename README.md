# gh-tt

**Table of Contents**

- [Install](#install)
- [Syntax](#syntax)
- [Connect to a GitHub project (kanban)](#configuration)
- [Files to ignore](#files-to-ignore)
- [Some neat tricks](#optional-configuration)
- [Feature requests](#feature-request-and-discussions)

**Addendum**
 - [The opinionated .tech that workflow](docs/workflow.md)
 - [How we work with _mentorship_ over _pull requests_](docs/responsibles.md)

## Purpose

This utility supports the workflow used by the _.tech that_ full-stack team within _.the tech collective_. It is designed as an [opinionated flow](docs/workflow.md). If you share our values and like our process, you can easily set this up for your own team.

## Install

This utility is a GitHub Command Line extension.

Dependencies:

- `python3` – any version, but developed and tested on v3.13. No additional Python dependencies ([install Python](https://www.python.org/downloads/))
- `gh` – the GitHub Command Line Interface ([install GitHub CLI](https://github.com/cli/cli#installation))

Once you have both dependencies installed, run:

```sh
gh extension install thetechcollective/gh-tt
```

The extension requires write access to projects. If you don't have it, you'll be prompted with instructions.

## Syntax

Run `gh tt -h` to see the syntax.

The extension provides three subcommands: `workon`, `wrapup`, and `deliver`. See the [workflow](docs/workflow.md) for details.

```
usage: gh tt [-h] [-v] {workon,wrapup,deliver} ...

positional arguments:
  {workon,wrapup,deliver}
    workon              Set the issue number context to work on
    wrapup              Commit the state of the current issue branch and push it to the remote
    deliver             Create a collapsed 'ready' branch for the current issue branch and push it to the remote

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output
```

### Workon

```
usage: gh tt workon [-h] [-v] [-i ISSUE | -t TITLE] [--assign | --no-assign]

options:
  -h, --help         show this help message and exit
  -v, --verbose      Enable verbose output
  -i, --issue ISSUE  Issue number
  -t, --title TITLE  Title for the new issue
  --assign           Assign @me to the issue (default)
  --no-assign        Do not assign anybody to the issue
```

## Wrapup

```
usage: gh tt wrapup [-h] [-v] -m MESSAGE

options:
  -h, --help              show this help message and exit
  -v, --verbose           Enable verbose output
  -m, --message MESSAGE   Message for the commit
```

## Deliver

```
usage: gh tt deliver [-h] [-v]

It squashes the issue branch into a single commit and pushes it to the remote, using the same name as the issue branch but prefixed with 'ready/*'. A separate workflow should be defined for ready branches. It doesn't take any parameters.

Policies for delivery can be set in the configuration file `.tt-config.json`. See the README in `thetechcollective/gh-tt` for details.

options:
  -h, --help     show this help message and exit
  -v, --verbose  Enable verbose output
```

## Configuration

To connect `gh tt` to a project, configure the `.gitconfig` file in the root of your repository. It should contain:

```ini
[project]
  owner   = <github organization>
  number  = <project number>
  workon  = Status:In Progress
  deliver = Status:Delivery Initiated
```

Only `owner` and `number` are required.

`workon` and `deliver` show the default values used for the following events:

- **`workon`** adds the issue to the project and sets the status to `In Progress`. Ensure you have a status by that name, or specify your WIP status in `.gitconfig`.
- **`deliver`** sets the status in the project to `Delivery Initiated`. If you use a different status name, update `.gitconfig` accordingly.

## Files to ignore

Our setup may pollute the workspace with two files you might want to add to `.gitignore`:

```gitignore
.tt_cache
_temp.token
```

- `.tt_cache` is used to optimize execution. If you change project settings in `.gitconfig`, delete this cache.
- `_temp.token` is related to the optional configuration described below. It's created and used by `gh-login.sh`. You only need to add it to `.gitignore` if you use `gh-login.sh`.

## Optional configuration

We use devcontainers. For inspiration, see [`devcontainer.json`](.devcontainer/devcontainer.json) in this repo.

Note:

```json
"initializeCommand": "./.devcontainer/initializeCommand.sh",
"postCreateCommand": "./.devcontainer/postCreateCommand.sh",
```

Both are designed as one-liners and are placed in separate files.

[`initializeCommand.sh`](.devcontainer/initializeCommand.sh) uses [`gh-login.sh`](.devcontainer/gh-login.sh) to generate a token from your host machine and prepare it for reuse in the container by [`postCreateCommand.sh`](.devcontainer/postCreateCommand.sh). This allows your container to inherit your host's `gh auth` status.

Git does not natively support a `.gitconfig` file in the repository root. For `gh tt`, this doesn't matter, as we read the file explicitly. However, we add it in `postCreateCommand.sh`:

```sh
# Check if ../.gitconfig is already included; if not, add it
git config --local --get include.path | grep -e ../.gitconfig >/dev/null 2>&1 || git config --local --add include.path ../.gitconfig
```

You can now use `.gitconfig` at the repo level as intended. We also provide some useful aliases.

Another convenience in `postCreateCommand.sh` is importing [`.gh_alias.yml`](.gh_alias.yml):

```sh
gh alias import .gh_alias.yml --clobber
```

This creates shortcuts so you can run:

```sh
gh workon   # instead of gh tt workon
gh wrapup   # instead of gh tt wrapup
gh deliver  # instead of gh tt deliver
```

In `postCreateCommand.sh`, we also install our `gh` extensions so they're always available:

```sh
gh extension install thetechcollective/gh-tt
gh extension install lakruzz/gh-semver
```

## Feature request and discussions

Issues are open on the repo: [`thetechcollective/gh-tt`](https://github.com/thetechcollective/gh-tt/issues). If you experience errors, misbehavior, or have feature requests, feel free to join the discussion.
