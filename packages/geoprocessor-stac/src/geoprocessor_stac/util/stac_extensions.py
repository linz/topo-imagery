from enum import Enum


class StacExtensions(str, Enum):
    file = "https://stac-extensions.github.io/file/v2.0.0/schema.json"
    processing = "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
