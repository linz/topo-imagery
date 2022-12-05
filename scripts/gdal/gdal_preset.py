from typing import List, Optional

from linz_logger import get_log
from scripts.gdal.gdalinfo import gdal_info, GdalInfoBand


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


# Find a band from the color interpretation
def find_band(bands: List[GdalInfoBand], color: str) -> Optional[GdalInfoBand]:
    for band in bands:
        if band["colorInterpretation"] == color:
            return band
    return None


# Determine what band numbers to use for the "-b" overrides for gdal_translate
def get_gdal_band_offset(file: str) -> List[str]:
    info = gdal_info(file, False)

    bands = info["bands"]

    alpha_band = find_band(bands, "Alpha")
    alpha_band_info: List[str] = []
    if alpha_band:
        alpha_band_info.extend(["-b", str(alpha_band["band"])])

    # Grey scale imagery, set R,G and B to just the grey_band
    grey_band = find_band(bands, "Gray")
    if grey_band:
        grey_band_index = str(grey_band["band"])
        return ["-b", grey_band_index, "-b", grey_band_index, "-b", grey_band_index] + alpha_band_info

    band_red = find_band(bands, "Red")
    band_green = find_band(bands, "Green")
    band_blue = find_band(bands, "Blue")

    if band_red is None or band_green is None or band_blue is None:
        get_log().warn(
            "gdal_info_bands_failed", band_red=band_red is None, band_green=band_green is None, band_blue=band_blue is None
        )
        return ["-b", "1", "-b", "2", "-b", "3"] + alpha_band_info

    return ["-b", str(band_red["band"]), "-b", str(band_green["band"]), "-b", str(band_blue["band"])] + alpha_band_info


# Get a command to create a virtual file which has a cutline and alpha applied
def get_cutline_command(cutline: str) -> List[str]:
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
