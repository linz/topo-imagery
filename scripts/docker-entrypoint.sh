#!/bin/sh

set -o errexit

GDAL_VERSION="$(gdalinfo --version)"
export GDAL_VERSION

. /venv/bin/activate

exec "$@"
