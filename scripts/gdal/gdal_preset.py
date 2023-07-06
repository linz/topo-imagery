from typing import List, Optional

from linz_logger import get_log

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
    # Force everything into big tiff
    # this converts all offsets from 32bit to 64bit to support TIFFs > 4GB in size
    "-co",
    "bigtiff=yes",
]

DEM_LERC = [
    "-co",
    "compress=lerc",
    "-co",
    # Set Max Z Error to 1mm
    "max_z_error=0.001",
    # Force all DEMS to AREA to be consistent
    # input tiffs vary between AREA or POINT
    "-mo",
    "AREA_OR_POINT=AREA",
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

# Arguments to convert TIFF from 16 bits to 8 bits
CONVERT_16BITS_TO_8BITS = [
    "-ot",
    "Byte",
    "-scale",
    # 16 bit --> 2^16 = 65536 values --> 0-65535
    "0",
    "65535",
    # 8 bit --> 2^8 = 256 values --> 0-255
    "0",
    "255",
]


def get_gdal_command(preset: str, epsg: str, convert_from: Optional[str] = None) -> List[str]:
    """Build a `gdal_translate` command based on the `preset`, `epsg` code, with conversion to 8bits if required.

    Args:
        preset: gdal preset to use. Defined in `gdal.gdal_preset.py`
        epsg: the EPSG code of the file
        convert_from: Defaults to None.

    Returns:
        a list of arguments to run `gdal_translate`
    """
    get_log().info("gdal_preset", preset=preset)
    gdal_command: List[str] = ["gdal_translate"]

    gdal_command.extend(BASE_COG)
    # Force the source projection to an input EPSG
    gdal_command.extend(["-a_srs", f"EPSG:{epsg}"])

    if preset == "lzw":
        gdal_command.extend(SCALE_254_ADD_NO_DATA)
        gdal_command.extend(COMPRESS_LZW)
        gdal_command.extend(WEBP_OVERVIEWS)

    elif preset == "webp":
        gdal_command.extend(COMPRESS_WEBP_LOSSLESS)
        gdal_command.extend(WEBP_OVERVIEWS)

    elif preset == "dem_lerc":
        gdal_command.extend(DEM_LERC)

    if convert_from == "UInt16":
        gdal_command.extend(CONVERT_16BITS_TO_8BITS)

    return gdal_command


def get_cutline_command(cutline: Optional[str]) -> List[str]:
    """Get a `gdalwarp` command to create a virtual file (`.vrt`) which has a cutline applied and alpha added.

    Args:
        cutline: path to the cutline

    Returns:
        a list of arguments to run `gdalwarp`
    """

    gdal_command = [
        "gdalwarp",
        # Outputting a VRT makes things faster as its not recomputing everything
        "-of",
        "VRT",
        # Ensure the target has a alpha channel
        "-dstalpha",
    ]

    # Apply the cutline
    if cutline:
        gdal_command += ["-cutline", cutline]

    return gdal_command


def get_alpha_command() -> List[str]:
    """Get a `gdalwarp` command to create a virtual file (.vrt) which has an alpha added.

    Returns:
        a list of arguments to run `gdalwarp`
    """

    return [
        "gdalwarp",
        # Outputting a VRT makes things faster as its not recomputing everything
        "-of",
        "VRT",
        # Ensure the target has a alpha channel
        "-dstalpha",
    ]


def get_transform_srs_command(source_epsg: str, target_epsg: str) -> List[str]:
    """Get a `gdalwarp` command to transform the srs.

    Args:
        source_epsg: the EPSG code of the source file
        target_epsg: the EPSG code for the output file

    Returns:
        a list of arguments to run `gdalwarp`
    """
    return [
        "gdalwarp",
        "-of",
        "VRT",
        "-multi",
        "-wo",
        "NUM_THREADS=ALL_CPUS",
        "-s_srs",
        f"EPSG:{source_epsg}",
        "-t_srs",
        f"EPSG:{target_epsg}",
        "-r",
        "bilinear",
    ]
