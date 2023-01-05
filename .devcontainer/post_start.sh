#!/bin/bash
set -ex

git config --global --add safe.directory $1
poetry run pre-commit install-hooks