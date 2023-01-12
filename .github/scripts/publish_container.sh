#!/bin/bash

GIT_VERSION=$(git describe --tags --always --match 'v*')
XYZ_VERSION=${GIT_VERSION%-*-*}
XY_VERSION=${XYZ_VERSION%.*}
X_VERSION=${XY_VERSION%.*}

for version in "latest" ${X_VERSION} ${XY_VERSION} ${XYZ_VERSION} ${GIT_VERSION}; do
  docker tag topo-imagery ghcr.io/linz/topo-imagery:$version
  docker push ghcr.io/linz/topo-imagery:$version
done