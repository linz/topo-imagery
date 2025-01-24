from decimal import Decimal
from enum import Enum
from typing import Annotated

DEFAULT_NO_DATA_VALUE: Annotated[Decimal, "From the New Zealand National Aerial LiDAR Base Specification"] = Decimal(-9999)

SCALE_254_ADD_NO_DATA = ["-scale", "0", "255", "0", "254", "-a_nodata", "255"]
""" Scale imagery from 0-255 to 0-254 then set 255 as NO_DATA. 
Useful for imagery that does not have a alpha band.
"""
BASE_COG = [
    # Suppress progress monitor and other non-error output.
    "-q",
    # Output to a COG
    "-of",
    "COG",
    "-stats",
    # Tile the image int 512x512px images
    "-co",
    "blocksize=512",
    # Ensure all CPUs are used for gdal translate
    "-co",
    "num_threads=all_cpus",
    # If not all tiles are needed in the tiff, instead of writing empty images write a null byte
    # this significantly reduces the size of tiffs which are very sparse
    "-co",
    "sparse_ok=true",
    # Do not create BIGTIFF
    # An error will be raise by GDAL if it fails creating a tiff > 4GB in size
    "-co",
    "bigtiff=no",
    # Always ignore existing overviews so they are not created from already compressed overviews
    "-co",
    "overviews=ignore_existing",
]
DEM_LERC = [
    "-co",
    "compress=lerc",
    "-co",
    # Set Max Z Error to 1mm
    "max_z_error=0.001",
    "-co",
    # Set MAX Z ERROR OVERVIEW to 10cm
    "max_z_error_overview=0.1",
    # Force all DEMS to AREA to be consistent
    # input tiffs vary between AREA or POINT
    "-mo",
    "AREA_OR_POINT=Area",
    "-a_nodata",
    str(DEFAULT_NO_DATA_VALUE),
]
COMPRESS_LZW = [
    # Compress as LZW
    "-co",
    "compress=lzw",
    # Predictor creates smaller files, for RGB imagery
    "-co",
    "predictor=2",
]
COMPRESS_WEBP_LOSSLESS = [
    # Compress into webp
    "-co",
    "compress=webp",
    # Compress losslessly
    "-co",
    "quality=100",
]
WEBP_OVERVIEWS = [
    # When creating overviews also compress them into Webp
    "-co",
    "overview_compress=webp",
    # When resampling overviews use lanczos
    # see https://github.com/linz/basemaps/blob/master/docs/operator-guide/cog-quality.md
    "-co",
    "overview_resampling=lanczos",
    # Reduce quality of overviews to 90%
    "-co",
    "overview_quality=90",
]


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
