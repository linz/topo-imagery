FROM ghcr.io/astral-sh/uv:uv:0.11.14@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97 AS uv_source

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3@sha256:dab45abca3ca83695d442018692f4f8a0f41955871c57e6101d7f89a92375caa AS builder

# Avoid blocking `apt-get install` commands
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC

COPY --from=uv_source /uv /uvx /bin/

RUN apt-get update
# Install pipx and build dependencies
RUN apt-get install --assume-yes gcc libgeos-dev python3-dev

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

# Bundle production dependencies into /venv
ENV UV_PROJECT_ENVIRONMENT=/venv
RUN uv sync --verbose --frozen --no-dev --no-install-project

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
