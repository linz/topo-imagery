#!/bin/sh

set -o errexit

GDAL_VERSION="$(gdalinfo --version)"
export GDAL_VERSION
PDAL_VERSION="$(pdal --version)"
export PDAL_VERSION

. /venv/bin/activate

exec "$@"
