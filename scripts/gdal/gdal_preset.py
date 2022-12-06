from typing import List

from linz_logger import get_log

# Force the source projection as NZTM EPSG:2193
NZTM_SOURCE = ["-a_srs", "EPSG:2193"]

# Scale imagery from 0-255 to 0-254 then set 255 as NO_DATA
# Useful for imagery that does not have a alpha band
SCALE_254_ADD_NO_DATA = ["-scale", "0", "255", "0", "254", "-a_nodata", "255"]

BASE_COG = [
    # Suppress progress monitor and other non-error output.
    "-q",
    # Output to a COG
    "-of",
    "COG",
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
    # Force everything into big tiff
    # this converts all offsets from 32bit to 64bit to support TIFFs > 4GB in size
    "-co",
    "bigtiff=yes",
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
    # Comppress into webp
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
    # see https://github.com/linz/basemaps/blob/master/docs/imagery/cog.quality.md
    "-co",
    "overview_resampling=lanczos",
    # Reduce quality of overviews to 90%
    "-co",
    "overview_quality=90",
]


def get_gdal_command(preset: str) -> List[str]:
    get_log().info("gdal_preset", preset=preset)
    gdal_command: List[str] = ["gdal_translate"]

    gdal_command.extend(BASE_COG)
    gdal_command.extend(NZTM_SOURCE)

    if preset == "lzw":
        gdal_command.extend(SCALE_254_ADD_NO_DATA)
        gdal_command.extend(COMPRESS_LZW)

    elif preset == "webp":
        gdal_command.extend(COMPRESS_WEBP_LOSSLESS)

    gdal_command.extend(WEBP_OVERVIEWS)

    return gdal_command


def get_cutline_command(cutline: str) -> List[str]:
    """
    Get a "gdalwarp" command to create a virtual file (.vrt) which has a cutline applied and alpha added
    """

    return [
        "gdalwarp",
        # Outputting a VRT makes things faster as its not recomputing everything
        "-of",
        "VRT",
        # Apply the cutline
        "-cutline",
        cutline,
        # Ensure the target has a alpha channel
        "-dstalpha",
    ]
