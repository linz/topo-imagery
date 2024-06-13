#!/bin/sh

set -o errexit

. /venv/bin/activate

exec "$@"
