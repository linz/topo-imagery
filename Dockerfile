FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.5@sha256:551756b6fb08cae2620f67b16818fda4e56e5c58107070b8af84c5ccd8c30bae

RUN apt-get update
# Install pip
RUN apt-get install python3-pip -y
# Install Poetry
RUN pip install poetry

# Define the working directory for the following commands
WORKDIR /app

# Add Poetry config
COPY poetry.lock pyproject.toml /app/

# Install Python dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy Python scripts
COPY ./scripts/ /app/scripts/

ENV PYTHONPATH="/app"
ENV GTIFF_SRS_SOURCE="EPSG"

WORKDIR /app/scripts
