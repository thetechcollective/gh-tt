# How to create a new (pre)release using the `semver` command
## Release
### Bump

`gh tt semver bump ...` will create a tag that is compliant with the semver v2.0 spec. It will be created locally in your repository. Once it's created you should push it to your origin using 'git push --tags`

You can apply the  `--no-run` switch to preview the git command that command.
```sh
$ gh tt semver bump --minor --no-run
git tag -a -m "1.2.0
Bumped minor from version '1.1.0' to '1.2.0'" 1.2.0
```

If you run the same command but without the `--no-run` flag it will generate the same command - and execute it.
```sh
$ gh tt semver bump --minor
```

### Note
If you are using GitHub's releases then you probably want a nice release note to add when you create the release.
To create a release note, run:
```sh
$ gh tt semver note --filename temp/release_note.md
```

### Release
To create the GitHub release, run:
```sh
$ gh release create `gh tt semver` --latest --verify-tag --notes-file temp/release_note.md
```
The backtick execution of `gh tt semver` lists the current latest release - in the example it would be `1.1.0`


> [!TIP]
> For our own convenience we have added two git aliases
> ```sh
> release = "!f() { git push --tag && gh release create `gh semver` --latest --verify-tag  --notes-file $1; }; f"
> prerelease = "!f() { git push --tag && gh release create `gh semver --prerelease` --verify-tag --prerelease --notes-file $1 ; }; f"
> ```
> Which allows us to run:
> ```sh
> $ gh tt semver bump --minor
> $ git release `gh tt semver note temp/release_note.md`
> ```

## Prerelease
For doing a prerelease, use the `--pre` flag in the `semver bump` command:

```sh
$ gh tt semver bump --pre
$ git prerelease `gh tt semver note temp/release_note.md`
```

## Syntax

You can use the `-h` or `--help` flag to any subcommand to learn it's syntax.
You can use the `-v` or `--verbose` flag to any subcommand to force it to print out a trace (for debugging or learning).

The semver command supports three subcommands; `bump`, `list` and `note`

```shell
$ usage: gh tt semver [-h] [-v] {bump,list,note} ...

usage: gh tt semver [-h] [-v] {bump,list,note} ...

Supports reading and setting the current version of the repository in semantic versioning format. Versions are stored as tags in the repository.

positional arguments:
  {bump,list,note}
    bump            Bumps the current version of the repository in semantic versioning format
    list            Lists the version tags in the repository in semantic versioning format and sort order
    note            Generates a release note based on the set of current semver tags

options:
  -h, --help        show this help message and exit
  -v, --verbose     Enable verbose output
```

### `bump`

```shell
usage: gh tt semver bump [-h] [-v] (--major | --minor | --patch | --prerelease | --build) [-m MESSAGE] [--prefix PREFIX] [--no-sha]
                         [--run | --no-run]

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output
  --major               Bump the major version, breaking change
  --minor               Bump the minor version, new feature, non-breaking change
  --patch               Bump the patch version, bug fix or rework, non-breaking change
  --prerelease, --pre   Bump the prerelease version
  --build               Bump the build version
  -m MESSAGE, --message MESSAGE
                        Additional message for the annotated tag
  --prefix PREFIX       Prefix to prepend the tag valid for both releases and prereleases
  --no-sha              Do not include git SHA in build number when using --build
  --run                 Execute the command
  --no-run              Print the command without executing it
```


### `list`

### `note`