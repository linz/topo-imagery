from enum import Enum


class StacExtensions(str, Enum):
    file = "https://stac-extensions.github.io/file/v2.0.0/schema.json"
    eo = "https://stac-extensions.github.io/eo/v1.1.0/schema.json"
