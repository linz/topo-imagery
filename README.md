# Topo Imagery

[![GitHub Actions Status](https://github.com/linz/topo-imagery/workflows/Build/badge.svg)](https://github.com/linz/topo-imagery/actions)
[![Coverage: 100% branches](https://img.shields.io/badge/Coverage-100%25%20branches-brightgreen.svg)](https://pytest.org/)
[![Dependabot Status](https://badgen.net/badge/Dependabot/enabled?labelColor=2e3a44&color=blue)](https://github.com/linz/topo-imagery/network/updates)
[![License](https://badgen.net/github/license/linz/topo-imagery?labelColor=2e3a44&label=License)](https://github.com/linz/topo-imagery/blob/master/LICENSE)
[![Conventional Commits](https://badgen.net/badge/Commits/conventional?labelColor=2e3a44&color=EC5772)](https://conventionalcommits.org)
[![Code Style](https://badgen.net/badge/Code%20Style/black?labelColor=2e3a44&color=000000)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=2e3a44)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code Style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)

_A collection of Python scripts used to process imagery_

## Package

### [topo-imagery](https://github.com/linz/topo-imagery/pkgs/container/topo-imagery)

#### Container Description

The purpose of this Docker container is to run Python scripts which use the [GDAL library](https://gdal.org/). It is based on [`osgeo/gdal:ubuntu-small-3.6.1` Docker image](https://hub.docker.com/r/osgeo/gdal/).

##### Usage

###### Local

Example:

1. Build the Docker image:
   `docker build .`
2. Log into AWS with `AWS-CLI`
3. Run the following command

```bash
docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -e AWS_PROFILE 'image-id'  python create_polygons.py --uri 's3://path-to-the-tiff/image.tif' --destination 'destination-bucket'
```

## Container package

GitHub Actions automatically handles publishing a container to the GitHub Package Registry (`ghcr`) and AWS Elastic Container Registry (ECR).

A new container is published everytime a change is [merged to the `master` branch](https://github.com/linz/topo-imagery/blob/master/.github/workflows/containers.yml). This container will be tagged with the following:

- `latest`
- `github` version (example: `v1.1.0-2-ga1154e8`)

A new container is also published [when a release is merged to `master`](https://github.com/linz/topo-imagery/blob/master/.github/workflows/release-please.yml) (see section bellow). This container will be tagged with the following:

- `latest`
- `vX` (example: `v1`)
- `vX.Y` (example: `v1.2`)
- `vX.Y.Z` (example: `v1.2.4`)

You can see the tags in the [GitHub Packages page](https://github.com/linz/topo-imagery/pkgs/container/topo-imagery).

## Releases

[googleapis/release-please](https://github.com/googleapis/release-please) is used to support the release process.
Based on what has been merged to `master` (`fix`, `feat`, `feat!`, `fix!` or `refactor!`), the library generates a `changelog` based on the commit messages and create a Pull Request. This is triggered by this [GitHub Action](https://github.com/linz/topo-imagery/blob/master/.github/workflows/release-please.yml).

### Publishing

To publish a release, the Pull Request opened by `release-please` bot needs to be merged:

1. Open the PR and verify that the `CHANGELOG` contains what you expect in the release. If the latest change you expect is not there, double-check that a GitHub Actions is not currently running or failed.
2. Approve the PR
3. Add the `automerge` label and wait for the PR to be merged
4. Once the Pull Request is merged to `master` a [GitHub Action](https://github.com/linz/topo-imagery/blob/master/.github/workflows/release-please.yml) it creates the release and publish a new container tagged for this release.
