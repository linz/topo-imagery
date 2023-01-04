#!/bin/bash
set -ex

WORKSPACE_DIR=$(pwd)

# Change Poetry settings to better deal with working in a container
#poetry config cache-dir ${WORKSPACE_DIR}/.cache
#poetry config virtualenvs.in-project true

# Install all dependencies
poetry config virtualenvs.create false
poetry install --no-interaction --no-ansi

#poetry shell
