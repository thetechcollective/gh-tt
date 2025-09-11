---
title: "Semantic Versioning with gh-tt"
description: "How to manage versioning in your repository using gh-tt semver"
author: "The Tech Collective"
theme: "lakruzz"
transition: "slide"
separators:
  section: '\n\n---\n---\n\n'
  slide: '\n\n---\n\n'
reveal: https://reveals.thetechcollective.dev/markdownloader/?owner=thetechcollective&repo=gh-tt&file=docs/semver-command.md
---

# Semantic Versioning with gh-tt

A guide to using the `semver` command in gh-tt

<!-- .element: style="text-align:center" -->

---

## Overview

The `gh tt semver` command helps you:

- Track version numbers using git tags
- Create and manage releases following semver spec
- Generate release notes automatically
- Push changes to GitHub

<!-- .element: style="text-align:left; font-size:35px" -->

---

## Quick Start Commands

```sh
# Get the current version
gh tt semver

# Get the current prerelease
gh tt semver --prerelease

# Create a new version tag
gh tt semver bump [--major|--minor|--patch|--build|--pre]

# Generate release notes
gh tt semver note
```

<!-- .element: style="font-size:30px" -->

---
---

# Basic Commands

---

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

<!-- .element: style="font-size:30px" -->

---

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

<!-- .element: style="font-size:28px" -->

---

## Preview Tag Creation

You can preview the tag command without executing it:

```sh
$ gh tt semver bump --minor --no-run
git tag -a -m "1.2.0
Bumped minor from version '1.1.0' to '1.2.0'" 1.2.0
```

<!-- .element: style="font-size:30px" -->

Note:
The --no-run flag is very helpful when you want to check what would happen without actually creating the tag.

---
---

# Working with Prereleases

---

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

<!-- .element: style="font-size:30px" -->

---

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

<!-- .element: style="font-size:30px" -->

---
---

# Release Notes

---

## Generating Release Notes

Create release notes from changes since the last tag:

```sh
# Generate notes to stdout
$ gh tt semver note

# Save notes to a file
$ gh tt semver note --filename temp/release_note.md
```

<!-- .element: style="font-size:30px" -->

---

## Notes Between Specific Versions

Specify the start and end points for the notes:

```sh
# From a specific version to current HEAD
$ gh tt semver note --from v1.1.0

# Between two specific versions
$ gh tt semver note --from v1.1.0 --to v1.2.0
```

<!-- .element: style="font-size:30px" -->

---
---

# Complete Workflows

---

## Creating a Full Release

Complete workflow to create and publish a release:

```sh
# Create a new version tag
$ gh tt semver bump --minor

# Generate release notes
$ gh tt semver note --filename temp/release_note.md

# Push the tag to origin
$ git push --tags

# Create the release on GitHub
$ gh release create `gh tt semver` \
  --verify-tag \
  --notes-file temp/release_note.md
```

<!-- .element: style="font-size:22px" -->

---

## Command Substitution

You can use command substitution for more compact workflows:

```sh
# Generate notes from latest release to a new build
$ gh tt semver note \
  --from `gh tt semver` \
  --to `gh tt semver bump --build` \
  --file temp/release_note.md

# Push tags and create release
$ git push --tags
$ gh release create `gh tt semver` \
  --verify-tag \
  --notes-file temp/release_note.md
```

<!-- .element: style="font-size:22px" -->

---

## Useful Git Aliases

For convenience, consider adding these git aliases:

```sh
# For official releases
release = "!f() { git push --tag && \
  gh release create `gh tt semver` \
  --latest --verify-tag --notes-file $1; }; f"

# For prereleases
prerelease = "!f() { git push --tag && \
  gh release create `gh tt semver --prerelease` \
  --verify-tag --prerelease --notes-file $1; }; f"
```

<!-- .element: style="font-size:20px" -->

---

## Using Git Aliases

With the aliases defined, you can use:

```sh
# Create a minor version bump and release
$ gh tt semver bump --minor
$ git release temp/release_note.md

# Create a prerelease
$ gh tt semver bump --pre
$ git prerelease temp/release_note.md
```

<!-- .element: style="font-size:30px" -->

---
---

# Advanced Usage

---

## Getting Help

All subcommands support help flags:

```sh
# Main help
$ gh tt semver --help

# Subcommand help
$ gh tt semver bump --help
$ gh tt semver list --help
$ gh tt semver note --help
```

<!-- .element: style="font-size:30px" -->

---

## Verbose Mode

For debugging or learning purposes, add the verbose flag:

```sh
$ gh tt semver -v bump --minor
```

This will print detailed information about what's happening behind the scenes.

<!-- .element: style="font-size:30px" -->

---

## List All Version Tags

View all semver-compliant tags in the repository:

```sh
$ gh tt semver list
```

<!-- .element: style="font-size:30px" -->

---

## Questions?

Thank you for learning about the `gh tt semver` command!

For more details, check out the [documentation](https://github.com/thetechcollective/gh-tt/blob/main/docs/semver_how_to_release.md).

<!-- .element: style="font-size:30px" -->

Note:
The semver command is designed to make semantic versioning easy and consistent across projects. Feel free to ask if you have any specific questions about any of the features or workflows.
