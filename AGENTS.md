# Agent Instructions for gh-tt

## Project overview

`gh-tt` is a GitHub CLI extension (written in Python) that automates a trunk-based development workflow. The main commands are `workon` (start work on an issue) and `deliver` (enable auto-merge on a PR). It is installed and invoked via `gh extension`.

## Running commands
This project uses `just` to run commands.

Execute `just` to see the list of available commands.


## CONTRIBUTING.md
Refer to @CONTRIBUTING.md for project structure and testing.

### Testing
Always run unit tests before running end to end tests. Only the following two commands are relevant for testing.
```sh
# Unit testing
uv run --frozen -- pytest -m 'not end_to_end and not legacy' --tb=no -q --no-header

# End to end testing
uv run --frozen -- python scripts/install_local_gh_tt.py
uv run --frozen -- pytest --numprocesses=auto -m end_to_end {{ args }}
```

### Deprecated code
`src/gh_tt/classes/` are largely deprecated. They are excluded from `ruff format`, `ty` type checking, and several test files within are excluded from tooling. Do not extend or refactor code in these directories unless explicitly asked.
