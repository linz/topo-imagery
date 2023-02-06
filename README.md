# Topo Imagery

[![GitHub Actions Status](https://github.com/linz/topo-imagery/workflows/Build/badge.svg)](https://github.com/linz/topo-imagery/actions)
[![Coverage: 100% branches](https://img.shields.io/badge/Coverage-100%25%20branches-brightgreen.svg)](https://pytest.org/)
[![Kodiak](https://badgen.net/badge/Kodiak/enabled?labelColor=2e3a44&color=F39938)](https://kodiakhq.com/)
[![Dependabot Status](https://badgen.net/badge/Dependabot/enabled?labelColor=2e3a44&color=blue)](https://github.com/linz/topo-imagery/network/updates)
[![License](https://badgen.net/github/license/linz/topo-imagery?labelColor=2e3a44&label=License)](https://github.com/linz/topo-imagery/blob/master/LICENSE)
[![Conventional Commits](https://badgen.net/badge/Commits/conventional?labelColor=2e3a44&color=EC5772)](https://conventionalcommits.org)
[![Code Style](https://badgen.net/badge/Code%20Style/black?labelColor=2e3a44&color=000000)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=2e3a44)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code Style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)

_A collection of Python scripts used to process imagery_

# Package

## [topo-imagery](https://github.com/linz/topo-imagery/pkgs/container/topo-imagery)

### Container Description

The purpose of this Docker container is to run Python scripts which use the [GDAL library](https://gdal.org/). It is based on [`osgeo/gdal:ubuntu-small-3.6.1` Docker image](https://hub.docker.com/r/osgeo/gdal/).

#### Usage

##### Local

Example:

1. Build the Docker image:
   `docker build .`
2. Log into AWS with `AWS-CLI`
3. Run the following command

```bash
docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -e AWS_PROFILE 'image-id'  python create_polygons.py --uri 's3://path-to-the-tiff/image.tif' --destination 'destination-bucket'
```

# Versioning and Release

[googleapis/release-please](https://github.com/googleapis/release-please) is used to support the release process.
The library generates a `changelog` based on the commit messages.
