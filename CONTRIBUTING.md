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
│       ├── classes/ # contains deprecated files
│       ├── commands/ # calls to external dependencies (non-pure functions)
│       │   ├── gh.py # calls to the GitHub CLI
│       │   └── git.py # calls to git
│       ├── deliver.py # main orchestrator for the `deliver` CLI command
│       ├── gh_tt.py # entrypoint of the application
│       ├── modules/
│       │   ├── tt_handlers.py # dispatching commands depending on args
│       │   └── tt_parser.py # CLI argument parsing
│       ├── shell.py # utility module for executing external processes
│       └── workon.py # main orchestrator for the `workon` CLI command
├── tests/
└── uv.lock # lockfile
```

## Commands
For convenience, `just` is used as a command runner. The most common commands are defined in the `justfile`.

To see available commands, execute `just`.

## Testing
`pytest` is used as the test framework. `hypothesis` is used for property-based testing. For other testing dependencies, look at the `dev` dependency group in `pyproject.toml`.

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