#!/bin/bash

GIT_VERSION=$(git describe --tags --always --match 'v*')
XYZ_VERSION=${GIT_VERSION%-*-*}
XY_VERSION=${XYZ_VERSION%.*}
X_VERSION=${XY_VERSION%.*}

for version in ${GIT_VERSION} ${XYZ_VERSION} ${XY_VERSION} ${X_VERSION} "latest"; do
  docker tag topo-imagery ghcr.io/paulfouquet/topo-imagery:$version
  docker push ghcr.io/paulfouquet/topo-imagery:$version
done