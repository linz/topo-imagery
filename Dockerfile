FROM ghcr.io/astral-sh/uv:0.11.25@sha256:1e3808aa9023d0980e7c15b1fa7c1ac16ff35925780cf5c459858b2d693f01a9 AS uv_source

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3@sha256:dab45abca3ca83695d442018692f4f8a0f41955871c57e6101d7f89a92375caa AS builder

# Avoid blocking `apt-get install` commands
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC

RUN apt-get update
# Install build dependencies
RUN apt-get install --assume-yes gcc libgeos-dev python3-dev
COPY --from=uv_source /uv /uvx /bin/

# Add UbuntuGIS PPA and install PDAL
RUN apt-get install --assume-yes software-properties-common apt-transport-https

# FIXME: This is using the "unstable" PPA as the stable one does not yet support Ubuntu 24.04 LTS (Noble Numbat). This should be changed to the stable PPA as soon as it supports Noble.
# See: https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa/+packages?field.name_filter=pdal&field.status_filter=published&field.series_filter=
RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update
RUN apt-get install -y pdal=2.6.2+ds-1~noble2
RUN mkdir /pdal_shared
RUN cp -nv $( ldd /usr/bin/pdal | awk '{print $3}' ) /pdal_shared/

# Define the working directory for the following commands
WORKDIR /src

# Add uv config
COPY uv.lock pyproject.toml /src/
COPY ./packages/ /src/packages/

# Bundle production dependencies into /venv
ENV UV_PROJECT_ENVIRONMENT=/venv
RUN uv sync --verbose --frozen --no-dev --no-install-project --no-editable

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3@sha256:dab45abca3ca83695d442018692f4f8a0f41955871c57e6101d7f89a92375caa

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH
ARG GIT_VERSION
ENV GIT_VERSION=$GIT_VERSION

ENV TZ=Etc/UTC

# Copy just the bundle from the first stage
COPY --from=builder /venv /venv

# Copy PDAL and shared libs from the builder stage
COPY --from=builder /usr/bin/pdal /usr/bin/pdal
COPY --from=builder /pdal_shared/ /usr/lib/

# Copy Python scripts
COPY ./scripts/ /app/scripts/

ENV PYTHONPATH="/app"
ENV GTIFF_SRS_SOURCE="EPSG"

WORKDIR /app/scripts

ENTRYPOINT ["./docker-entrypoint.sh"]
