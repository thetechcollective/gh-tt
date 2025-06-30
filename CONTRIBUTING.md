# Contributing


## Our extension our rules!
Feel free to create a fork and fool around - following your own rules. But if you wish any of your contributions to be merged into the product's `main` prepare a pull request in your own fork.

If you are a trusted contributor and already have write acces to the repo, consider:

1. No commit can be accepted on _our_ `main`, unless it references a [GitHub issue](https://github.com/thetechcollective/gh-tt/issues)[^issue] in the commit message.
2. Development branches must be created using `gh tt workon` - so they refer to the issue they belong to.
3. Development branches with more than one commit must all reference the issue they belong to - `gh tt wrapup` does that for you!
4. Development branches must be squezeed to branches with just one single commit that can be merged _fast-forward only_. These branches must be prefixed with `ready/` to trigger the right workflow. `gh tt deliver` does that for you.
5. Coverage on all unittests should be at least the same percentage — or higher, as it was in the commit you branched out from.

[^issue]: If there isn't any issue to work on, feel free to create it. The repo is Open Source, and while you don't have access to push to main, you do have access to create new issues.

## Development
The development environment is designed to be run from the devcontainer defined in the repo. Simply start it up in VS Code and run the container locally in Docker or run it in a GitHub codespace.

The `postCreateCommand` will intilize the `venv` and do a `uv sync` to use by running to install the dependencies defined in `uv.lock`.

After that, you should do **ONE THING manually**😱[^manual]: In the Command Palette in VC Code search for and select `Python: Select interpreter...`. Choses to use the interpreter defined by `.vscode/settings.json` file.

[^manual]: This is not ideal, but we havn't figured out how to add this specific setting to the configuration - please chip in with suggestions if you know how!

### Testing
You can run unit tests with pytest
```sh
pytest -m unittest
```

With coverage
```sh
pytest --cov=. --cov-config=.coveragerc -m unittest
```

You can also use VS Code's "Testing" tab to run unit tests. It should work out of the box with the settings in `.vscode/settings.json`.

To run `gh tt` with the changes you have on your dev branch, you can run the entry script

E.g. to run `wrapup` using the code on the current branch 
```sh
./gh-tt wrapup -m "Fix"
```