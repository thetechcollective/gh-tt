#!/usr/bin/env bash

RELEASE=$(gh tt semver)
PRERELEASE=$(gh tt semver --prerelease)

echo "## Prerelease $PRERELEASE">temp/.prerelease_note   
echo "#### Listing [all changes](../../compare/$RELEASE..$PRERELEASE) since last release ($RELEASE)">>temp/.prerelease_note 
git log --format='%n- **%cd**: %s%n%h %an' --date=format:'%Y-%m-%d'  `gh semver`..`gh semver --prerelease`>>temp/.prerelease_note   
