#!/bin/bash

input=$1
output=$2
preset=$3

docker run  -v ${HOME}/tmp/:/tmp/ topo-imagery python3 standardise_validate.py --from-file $input --preset $preset --target-epsg 2193 --source-epsg 2193 --target /tmp/ --collection-id 123 --start-datetime 2023-01-01 --end-datetime 2023-01-01
cmp --silent ${HOME}/tmp/$output ./scripts/tests/data/output/$output
rm ${HOME}/tmp/$output