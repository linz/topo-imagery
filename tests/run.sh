#!/bin/bash

docker build -t topo-imagery .

sh ./tests/standardise.sh tests/data/aerial.json BG35_1000_4829.tiff webp
#sh ./tests/standardise.sh tests/data/dem.json BG35_1000_4829.tiff webp