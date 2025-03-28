#!/usr/bin/env bash

set -e

PREFIX="$(basename $0): "

pipenv sync --dev
git config --local --get include.path | grep -e ../.gitconfig || git config --local --add include.path ../.gitconfig

$(dirname $0)/gh-login.sh postcreate
gh extension install thetechcollective/gh-tt
gh extension install lakruzz/gh-semver
gh alias import .gh-alias.yml --clobber
