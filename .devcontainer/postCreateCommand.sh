#!/usr/bin/env bash

pipenv sync --dev
git config --local --get include.path | grep -e ../.gitconfig || git config --local --add include.path ../.gitconfig