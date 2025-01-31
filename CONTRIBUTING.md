# Contributing


## My extension my rules!
Create a fork and fool around - following your own rules. But if you wish any of your contributions merged into the product's `main` prepare a pull request in your own fork and consider:

1. No commit can be accepted on _our_ `main`, unless it references a [GitHub issue](https://github.com/lakruzz/gh-semver/issues)[^issue] in the commit message.
2. Development branches must be [clearly marked which issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-a-branch-for-an-issue) they refer to.
3. Develompent branches with more than one commit not reachable from `main` will be _squashed_ in to main (so you may as well just squash it yourself) - keep the commit message on branch tip crip!
4. Development branches must be _fast-forward only_ when merged into _our_ `main`. You can achieve this by _always_ syncing your fork and rebasing your dev branch against _our_ `main` before you create the pull request.
5. Coverage on all unittests should be at least the same percentage — or higher, as it was in the commit you branhced out from.

[^issue]: If there isn't any issue to work on, feel free to create it. The repo is Open Source, and while you don't have access to push to main, you do have access to create new issues.

## Development
The development environment is designed to be run from the devcontainer defined in the repo. Simply start it up in VS Code and run the container locally in Docker or run it in a GitHub codespace.

The `postCreateCommand` will intilize the pipenv to use by running

```
pipenv sync
```

This will create the `venv` and install the dependncies defined in `Pipfile.lock`.

After that, you should do **ONE THING manually**😱[^manual]: In the Command Palette in VC Code search for and select `Python: Select interpreter...`. It's likely that you are presented with several options. You should pick the one that specifically mentions `(gh-semver*)` in the title.

[^manual]: This is not ideal, but I havn't figured out how to add this specific setting to the configuration - please chip in with suggestions if you know how!

<img src="https://github.com/user-attachments/assets/92391bee-ffe4-473e-b83a-900dcac4cf52" align="right"/>
Now you are good to go - start by going to the testing console and let see that the test discovery runs without any issues. After that you should see two test suites:

- `test_gh-semver-smoketest.py`
- `test_gh-semver-unittests.py`

You should mainly pay attention to the the unittests. Run them. And run them again _with coverage_. If you wish to contribute to this product you should at least gurantee that coverage is the same or higher when you push to main.

The shell script `gh-semver` is not included in the tests, but you can run it from the terminal like this:

```
./gh-semver
```

You can also execute the extension as a locally installed gh extension.

To install the extenison locally it's required that you gh is set up right

```shell
gh auth status # should say that you are successfull y logged in if not run...
gh auth login -p https -h github.com --web # run gh authl login -h to learn more details
```

When you are authenticated correctly install is like this:

```shell
gh extension install . 
gh semver # after the install you can use gh to invoke it. use 'gh extension remove gh-semver' to remvoe it
```

Note that end-users will install it using the global syntax:

```shell
gh extension install lakruzz/gh-semver # it will pull latest version from GitHub
gh extension upgrade gh-semver # 'upgrade' is not supported on extenions installed with the locla syntax
```

Your feedback - or requst for help - is always welcome: Use [the Issues on GitHub](https://github.com/lakruzz/gh-semver/issues) to communicate.
