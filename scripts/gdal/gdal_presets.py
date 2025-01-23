from enum import Enum


class CompressionPreset(str, Enum):
    """Enum for the different compression presets available for standardising TIFFs."""

    DEM_LERC = "dem_lerc"
    LZW = "lzw"
    WEBP = "webp"


class HillshadePreset(str, Enum):
    """Enum for the different type of hillshade available for generating from a DEM."""

    GREYSCALE = "greyscale"  # Standard/default hillshade
    IGOR = "igor"  # Whiter hillshade (see http://maperitive.net/docs/Commands/GenerateReliefImageIgor.html)
    MULTIDIRECTIONAL = "multidirectional"
