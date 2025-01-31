# gh-semver

**This utility is desinged as a GitHub Command Line extension.**



<details><summary><h2>Syntax</h2></summary>

Use the `-h` switch to lean the syntax 

```
gh tt workon <issue:integer>                 # Will begin or resume work on an issue.
gh tt workon -t, --title <title:text>        # Will open a new issue, and begin work on that issue.

gh tt wrapup -m, [--message <message:text>]  # Will collapse the dev branch into just one commit.
                                             # Rebase it, push it and create a pull-request 

gh tt comment -m, --message <message::text>  # Adda  comment to the issue related to hte dev branch

```

## Note
It's written in Python and runs in a `pipenv` so it doesn't leave any footprint or alterization to your own, current Python setup. All requirements besides `python3` are managed independenly by the script itself.
