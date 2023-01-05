# topo-imagery devcontainer

The purpose of this devcontainer is to avoid any trouble to the developers managing a Python environment with GDAL and other dependencies.

> **_NOTE:_** It has been setup to be used with VSCode under a linux environment. Some functionalities might not work with a different configuration.

## `Dockerfile`

This Docker container describes the OS configuration for the development environment. It is intended to be based on the same Docker image than our production container.

## `devcontainer.json`

It allows us to use common settings for the development environment.

### `post_create.sh`

This script is run after the container is created.

## Usage

Once opened the local cloned repository in VSCode, click on the bottom left corner green button `><` `Open a Remote Window` and select the `Reopen in Container` option. Wait for the container to be build. Open a new terminal from VSCode. It should source the Python `venv`.
