#!/bin/bash
set -e
# Install all dependencies with poetry
poetry install --no-interaction
git config --global --add safe.directory $1
poetry run pre-commit install