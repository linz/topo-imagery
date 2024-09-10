from enum import Enum


class Preset(str, Enum):
    DEM_LERC = "dem_lerc"
    LZW = "lzw"
    WEBP = "webp"
