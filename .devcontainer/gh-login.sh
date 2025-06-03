#!/usr/bin/env bash
# gh-login.sh

# Usage: ./gh-login.sh {initialize|postcreate}"
#
# Purpose: To allow the devcontainer to authenticate with GitHub CLI without user interaction
#
# Designed to run as an initializeCommand in a devcontainer.json file
# This script will check if the host is authenticated with GitHub CLI
# If so it will store the base64 encoded token in the _temp.token file
# for a later postCreateCommand to use to authenticate the devcontainer with GitHub CLI
# 
# To get the benefits of this script, you must have the following in your devcontainer.json file:
#
#   "initializeCommand": "./.devcontainer/gh-login.sh initialize",
#   "postCreateCommand": "./.devcontainer/gh-login.sh postcreate",


# Failure is not an option:
set -e

initialize() {  
  gh auth status > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "$PREFIX Your host is not authenticated with GitHub CLI."
    echo "$PREFIX NOTE:"
    echo "$PREFIX    In the future, make sure your host is authenticated with GitHub CLI" 
    echo "$PREFIX    at the time you start the devconatiner."
    echo "$PREFIX    And the devcontainer will be able to log you in without user intaraction."
  else
    echo "$PREFIX Your host is authenticated with GitHub CLI - Capturing your token for reuse."
    token=$(gh auth token)
    echo $(echo $token) | base64 > $(dirname $0)/_temp.token
  fi
}

postcreate(){
  if [ -e $(dirname $0)/_temp.token ]; then
      echo "$PREFIX $(dirname $0)/_temp.token exists, continuing with login"
      echo "$PREFIX ...using token from host"
      cat $(dirname $0)/_temp.token | base64 --decode | gh auth login --with-token
      echo "$PREFIX ...cleaning up after the initialize step"
      rm -f $(dirname $0)/_temp.token       
      echo "$PREFIX Logged in to GitHub CLI - account status:"
      gh auth status
  else
      gh auth login -w -p https -h github.com
  fi
}


## MAIN

PREFIX="🐙  "
if [ "$1" = "initialize" ]; then
  echo "$PREFIX Running $(basename $0) initialize"  
  initialize
elif [ "$1" = "postcreate" ]; then
  echo "$PREFIX Running $(basename $0) postcreate"  
  postcreate
else
  echo "Usage: $(basename $0) {initialize|postcreate}"
  exit 1
fi
echo "$PREFIX SUCCESS"
exit 0