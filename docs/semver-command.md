# Semantic Versioning with gh-tt

A guide to using the `semver` command in gh-tt

## Overview

The `gh tt semver` command helps you:

- Track version numbers using git tags
- Push changes to GitHub

## Quick Start Commands

```sh
# Get the current version
gh tt semver

# List all semver tags
gh tt semver list

# Get the current prerelease
gh tt semver --prerelease

# Create a new version tag
gh tt semver bump [--major|--minor|--patch|--build|--pre]
```

## Getting the Current Version

To see the highest preceding semver compliant release tag:

```sh
$ gh tt semver
1.2.3
```

For prerelease tags:

```sh
$ gh tt semver --prerelease
1.2.4-pre.1
```

## Creating New Version Tags

Create tags that comply with the [Semantic Versioning 2.0 spec](https://semver.org/):

```sh
# Bump the major version (breaking changes)
$ gh tt semver bump --major    # e.g., 1.2.3 → 2.0.0

# Bump the minor version (new features)
$ gh tt semver bump --minor    # e.g., 1.2.3 → 1.3.0

# Bump the patch version (bug fixes)
$ gh tt semver bump --patch    # e.g., 1.2.3 → 1.2.4
```


## Preview Tag Creation

You can preview the tag command without executing it:

```sh
$ gh tt semver bump --minor --no-run
git tag -a -m "1.2.0
Bumped minor from version '1.1.0' to '1.2.0'" 1.2.0
```

Note:
The --no-run flag is very helpful when you want to check what would happen without actually creating the tag.

## Creating a Prerelease

Add the `--pre` flag to create prerelease versions:

```sh
# Create a prerelease
$ gh tt semver bump --pre
1.2.3-pre.1

# Bump the build number on a prerelease
$ gh tt semver bump --build
1.2.3-pre.2
```

## Including Build Numbers

You can also append build numbers to versions:

```sh
# Add a build number
$ gh tt semver bump --build
1.2.3+1

# Exclude git SHA from build number
$ gh tt semver bump --build --no-sha
1.2.3+1
```