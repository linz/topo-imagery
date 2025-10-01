FROM pdal/pdal:2.9.2@sha256:18d73101500cd673052ee4ead8a4b716a9dad09c8711e88e7a37abed2496c469 AS builder

# Avoid blocking `apt-get install` commands
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC

RUN apt-get update
# Install pipx and build dependencies
RUN apt-get install --assume-yes gcc libgeos-dev pipx python3-dev
# Install Poetry with the bundle plugin
RUN pipx install poetry
RUN pipx inject poetry poetry-plugin-bundle

# Define the working directory for the following commands
WORKDIR /src

# Add Poetry config
COPY poetry.lock pyproject.toml /src/

# Bundle production dependencies into /venv
RUN /root/.local/bin/poetry bundle venv --no-ansi --no-interaction --only=main -vvv /venv


FROM pdal/pdal:2.9.2@sha256:18d73101500cd673052ee4ead8a4b716a9dad09c8711e88e7a37abed2496c469

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH
ARG GIT_VERSION
ENV GIT_VERSION=$GIT_VERSION

ENV TZ=Etc/UTC
# Copy just the bundle from the first stage
COPY --from=builder /venv /venv

# Copy Python scripts
COPY ./scripts/ /app/scripts/

ENV PYTHONPATH="/app"
ENV GTIFF_SRS_SOURCE="EPSG"

WORKDIR /app/scripts

ENTRYPOINT ["./docker-entrypoint.sh"]
