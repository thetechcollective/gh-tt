# How to create a new (pre)release using the `semver` command
## Release
### Bump
The first step is to create the release tag locally, in your repository. You can use the `gh tt semver bump` subcommand.

Let's use the `--no-run` switch to preview the command.
```sh
$ gh tt semver bump --minor --no-run
git tag -a -m "1.2.0
Bumped minor from version '1.1.0' to '1.2.0'" 1.2.0
```

To create the tag "for real", execute the command without the `--no-run` flag.
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
For doing a prerelease, add the `--prerelease` flag to `semver bump`.

```sh
$ gh tt semver bump --minor --prerelease
$ git prerelease `gh tt semver note temp/release_note.md`
```