# gh-tt

**This utility is desinged as a GitHub Command Line extension.**

Install:

```
gh extension install thetechcollective/gh-tt
```

The extension requires that you have write access to projects too

Run `gh tt -h` to learn the syntax


The extension has three subcommands `workon`, `wrapup` and `deliver`. 

```shell
usage: gh tt [-h] [-v] {workon,wrapup,deliver} ...

positional arguments:
  {workon,wrapup,deliver}
    workon              Set the issue number context to work on
    wrapup              Collapse dev branch into one commit, check or set the commit message
    deliver             Create the pull request for the current issue. Rebase and push the branch

options:
  -h, --help       show this help message and exit
  -v, --verbose    Enable verbose output
```

#### --help
You can always use the switch `--help` to learn details about a specific syntax

#### --verbose
You can always use the switch `--verbose` to have the extensions print out all underlying calls to the OS.
## gh workon

`workon` takes an `--issue` switch. you can use if you want to work on a specific issue in the current repo

E.g. `gh workon --issue 13`

Or you can use the `--title` switch if you want to work on an issue that doesn't yet exist, you apply the title for the issue you want created.

e.g. `gh workon --title "Some new issue"`

```shell
usage: gh tt workon [-h] [-v] [-i ISSUE | -t TITLE]

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output
  -i ISSUE, --issue ISSUE
                        Issue number
  -t TITLE, --title TITLE
                        Title for the new issue
```

In either case you will end up on a development branch referencing the issue. If a branch already exist either locally or remote, you'll reuse that if not a new branch will be created on the issue.

`Workon` will set the `Status` in the GitHub Project to `In Progress` and the `Start` date to today.

## gh wrapup


```shell
usage: gh tt wrapup [-h] [-v] 
options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output
```

`wrapup` will collapse you current branch into just one commit, and make sure that the commit message contains one of the closing keywords (e.g. "resolves #<issue>") so the issue will be closed when the commit arrives at the default branch (`main`).

In order to deliver you should be aware that a `rebase` against the default branch (`main`) is also needed, but it's not included in the automated `wrapup` process, simply because this is potentially an operation that will change the content of your branch. For that reason you should take full responsibility of that process yourself. In other words make it a habit to run `rebase` before the `wrapup`:

```shell
git rebase main
gh tt wrapup
```

## gh deliver

```shell
usage: gh tt deliver [-h] [-v] [--title TITLE]

options:
  -h, --help     show this help message and exit
  -v, --verbose  Enable verbose output
  --title TITLE  Title for the pull request - default is the issue title
```

`deliver` will try to rebase your branch and push it to origin if it succeeds it will create a pull request on the branch - if it doesnt exist already.

## Feature request and discussions

The Issues are open on the repo: [`thetechcollective.gh-tt`](https://github.com/thetechcollective/gh-tt/issues). If you experiencve any erros, misbekaviour or if you have feature requests, feel free to join the discussion.

## Note
It's written in Python and runs in a `pipenv` so it doesn't leave any footprint or alterization to your own, current Python setup. All requirements besides `python3` are managed independenly by the script itself.
