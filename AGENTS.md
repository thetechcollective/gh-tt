# Agent Instructions for gh-tt

## Project overview

`gh-tt` is a GitHub CLI extension (written in Python) that automates a trunk-based development workflow. The main commands are `workon` (start work on an issue) and `deliver` (enable auto-merge on a PR). It is installed and invoked via `gh extension`.

## Running commands
Prefix all commands with `uv run` to use the project's locked environment without modifying the user's shell.

Always run this command after making changes
```sh
ruff format && ruff check --fix && ty check
```

## CONTRIBUTING.md
Refer to @CONTRIBUTING.md for project structure and testing.

### Testing
Always run unit tests before running end to end tests. Only the following two commands are relevant for testing.
```sh
# Unit testing with coverage
uv run --frozen -- pytest --cov=. --cov-config=.coveragerc -m unittest

# End to end tests
uv run --frozen -- pytest -m end_to_end
```

### Deprecated code
`gh_tt/classes/` and `gh_tt/modules/` are largely deprecated. They are excluded from `ruff format`, `ty` type checking, and several test files within are excluded from tooling. Do not extend or refactor code in these directories unless explicitly asked.
