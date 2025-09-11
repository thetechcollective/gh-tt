# How to create a new release – or prerelease – using the `semver` command

# Quick guide:

`gh tt semver` will print the highest preceding semver compliant release tag

`gh tt semver --prerelease` will print the highest preceding semver compliant prerelease tag

`gh tt semver bump ...` will create a tag that is compliant with the semver [v2.0 spec.](https://semver.org/) It will be created locally in your repository. Once it's created you should push it to your origin using 'git push --tags`

You can apply the  `--no-run` switch to `bump` to preview the git command that command.
```sh
$ gh tt semver bump --minor --no-run
git tag -a -m "1.2.0
Bumped minor from version '1.1.0' to '1.2.0'" 1.2.0
```

If you run the same command but without the `--no-run` flag it will generate the same command - and execute it.
```sh
$ gh tt semver bump --minor
```

You can use `gh tt semver note` to generate release notes. The will be printed to `STDOUT` or a file if you choose

The following commands will bump the build sequence number, taking offset in the highest preceding. Generate a note, push tha tag and generate a prerelease on GitHub using that note
```sh
$ gh tt semver bump --build
$ gh tt semver note --filename temp/release_note.md
```

### backtick command substitution

`gh tt semver` prints the current latest release
`gh tt semver` prints the current latest prerelease
`gh tt semver note` with the file outputs the name of the file created
`gh tt semver bump ...` outputs that tag created

To advance the build number on the current prerelease and populate it to github , with a note containing all changes since the last official release:

```sh
$ gh tt semver note --from `gh tt semver` --to `gh tt semver bump --build` --file temp/release_note.md
$ git push tags
$ gh release create `gh tt semver --prerelease` --verify-tag --notes-file temp/release_note.md
````

> [!TIP]
> For our own convenience we have added two git aliases
> ```sh
> release = "!f() { git push --tag && gh release create `gh semver` --latest --verify-tag  --notes-file $1; }; f"
> prerelease = "!f() { git push --tag && gh release create `gh semver --prerelease` --verify-tag --prerelease --notes-file $1 ; }; f"
> ```
> Which allows us to run:
> ```sh
> $ gh tt semver bump --minor
> $ git release `gh tt semver note --notes-file temp/release_note.md`
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