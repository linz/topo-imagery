FROM osgeo/gdal:ubuntu-small-latest

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
    && poetry install --no-dev --no-interaction --no-ansi

# Copy Python scripts
COPY ./scripts/* /app/
