FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.0@sha256:3ca7c26ef3aff8c8d134bbaa62e13d1a4c97c8a7b2853f1db0ff34c2f939a4de

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
