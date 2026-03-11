# Contributing

The blessed way to work on this project is via the devcontainer specified in `.devcontainer/devcontainer.json`. It will install all necessary dependencies and set up VS Code for test running and debugging.

If you do not want to work in a devcontainer, check out what's happening in `postCreateCommand.sh` - you should be able to set up your environment by manually following the script.

## Project structure
```sh
. # repo root
├── gh-tt # entrypoint for the gh extension
├── gh_tt
│   ├── gh_tt.py # entrypoint of the application
│   ├── modules/
│   │   ├── tt_handlers.py # dispatching commands depending on args
│   │   └── tt_parser.py # CLI argument parsing
│   ├── deliver.py # main orchestrator for the `deliver` CLI command
│   ├── shell.py # utility module for executing external processes
│   ├── workon.py # main orchestrator for the `workon` CLI command
│   ├── commands/ # calls to external dependencies (non-pure functions)
│   │   ├── gh.py # calls to the GitHub CLI
│   │   └── git.py # calls to git
│   ├── classes/ # contains mostly deprecated part of the project
│   └── tests/ # automated testing
├── README.md
├── docs/ # documentation
├── pyproject.toml
└── uv.lock # lockfile
```

## Testing
`pytest` is used as the test framework. `hypothesis` is used for property-based testing. For other testing dependencies, look at the `dev` dependency group in `pyproject.toml`.

```sh
# Run unit tests
pytest -m unittest

# Run unit tests with coverage
pytest --cov=. --cov-config=.coveragerc -m unittest

# Run end to end tests
# Installs a local version of gh tt,
# so that you are executing tests against your changes
# not the gh-tt extension installed by your devcontainer
python scripts/install_local_gh_tt.py
pytest -m end_to_end
```

You can also use VS Code's "Testing" tab to run unit tests. It should work out of the box with the settings in `.vscode/settings.json`.

To run `gh tt` with the changes you have on your branch, you can run the entry script
```sh
./gh-tt deliver
```