#!/bin/bash
#
# Version bump the repo and create a branch ready for pull request
#
set -e

git checkout master
git pull --rebase

poetry version minor

# Set the version environment variable
CURRENT_VERSION=$(poetry version --short)

# Checkout a new release branch
git checkout -b release/v${CURRENT_VERSION}

# Commit the changed files
git commit -am "release: ${CURRENT_VERSION}"