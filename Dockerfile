FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0@sha256:d1a38af532e5d9e3991c4a6bddc2f2cb52644dc30a4eb8242101e8e23c3f83f6 AS builder
# Avoid blocking `apt-get install` commands
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC

RUN apt-get update
# Install pipx and build dependencies
RUN apt-get install --assume-yes gcc libgeos-dev pipx python3-dev

# Install Poetry with the bundle plugin
RUN pipx install poetry
RUN pipx inject poetry poetry-plugin-bundle

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

# Add Poetry config
COPY poetry.lock pyproject.toml /src/

# Bundle production dependencies into /venv
RUN /root/.local/bin/poetry bundle venv --no-ansi --no-interaction --only=main -vvv /venv


FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0@sha256:d1a38af532e5d9e3991c4a6bddc2f2cb52644dc30a4eb8242101e8e23c3f83f6
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
