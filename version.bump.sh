#!/bin/bash
#
# Version bump the repo and create a branch ready for pull request
#
set -e

git checkout master
git pull --rebase

uv version --bump minor

# Set the version environment variable
CURRENT_VERSION=$(uv version --short)

# Checkout a new release branch
git checkout -b release/v${CURRENT_VERSION}

# Commit the changed files
git commit -am "release: ${CURRENT_VERSION}"