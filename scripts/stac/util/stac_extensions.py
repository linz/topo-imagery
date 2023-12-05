from enum import Enum


class StacExtensions(str, Enum):
    file = "https://stac-extensions.github.io/file/v2.0.0/schema.json"
    linz = "https://stac.linz.govt.nz/v0.0.15/linz/schema.json"
