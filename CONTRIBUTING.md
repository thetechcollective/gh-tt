# Contributing

The blessed way to work on this project is via the devcontainer specified in `.devcontainer/devcontainer.json`. It will install all necessary dependencies and set up VS Code for test running and debugging.

If you do not want to work in a devcontainer, check out what's happening in `postCreateCommand.sh` - you should be able to set up your environment by manually following the script.

## Project structure
```sh
./ # repo root
├── docs/ # documentation
├── gh-tt # entrypoint of the gh extension
├── justfile # command runner configuration
├── logs/ # logs from test runners
├── pyproject.toml
├── README.md
├── scripts/ # helpers and utilities for working on the project
├── src/
│   └── gh_tt/
│       ├── cli/
│       │   ├── gh_tt.py # entrypoint of the application
│       │   ├── tt_handlers.py # dispatching commands depending on args
│       │   └── tt_parser.py # CLI argument parsing
│       ├── commands/ # calls to external dependencies (non-pure functions)
│       │   ├── gh.py # calls to the GitHub CLI
│       │   ├── git.py # calls to git
│       │   └── shell.py # utility module for executing external processes
│       ├── deliver.py # main orchestrator for the `deliver` CLI command
│       ├── legacy/ # contains deprecated files
│       └── workon.py # main orchestrator for the `workon` CLI command
├── tests/
└── uv.lock # lockfile
```

## Commands
For convenience, `just` is used as a command runner. The most common commands are defined in the `justfile`.

To see available commands, execute `just`.

## Testing
`pytest` is used as the test framework. `hypothesis` is used for property-based testing. For other testing dependencies, look at the `dev` dependency group in `pyproject.toml`.

`workon` and `deliver` are covered predominantly via end to end testing that runs against live GitHub APIs. This is because the vast majority of those commands are calls to git or gh cli, which makes function-level tests difficult without heavy mocking. Instead of risking that we do not test the underlying implementation when using mocks, there is the end to end tests that _actually_ run the code under test. 

Generally, you should feel confident that `workon` and `deliver` end to end testing will catch your mistakes. However, pay attention when changing polling for PR checks in `deliver` which does not have end to end tests.

`semver` is relatively well tested as well. However, more could be done to test semver at the boundary (as in end to end). You should confirm that your changes do the expected thing manually by running with the `--no-run` option.

```sh
# Run unit tests with coverage
just test

# Run end to end tests
just test-e2e
```

You can also use VS Code's "Testing" tab to run unit tests. It should work out of the box with the settings in `.vscode/settings.json`.

To run `gh tt` with the changes you have on your branch, you can run the entry script
```sh
# Run deliver with your local changes
just run deliver
```