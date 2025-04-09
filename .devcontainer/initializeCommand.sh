#!/usr/bin/env bash

set -e

PREFIX="👀  "
echo "$PREFIX Running $(basename $0)"

echo "$PREFIX Initializing  GH CLI"

$(dirname $0)/gh-login.sh initialize

echo "$PREFIX SUCCESS"
exit 0

