from __future__ import annotations

from decimal import Decimal

from linz_logger import get_log

from scripts.gdal.gdal_bands import get_gdal_band_offset
from scripts.gdal.gdal_helper import EpsgNumber
from scripts.gdal.gdal_presets import (
    BASE_COG,
    COMPRESS_LZW,
    COMPRESS_WEBP_LOSSLESS,
    COMPRESS_ZSTD,
    DEM_LERC,
    SCALE_254_ADD_NO_DATA,
    WEBP_OVERVIEWS,
    ZSTD_OVERVIEWS,
    CompressionPreset,
    HillshadePreset,
)
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.capture_area import get_buffer_distance


def get_gdal_command(preset: str, epsg: int) -> list[str]:
    """Build a `gdal_translate` command based on the `preset`, `epsg` code, with conversion to 8bits if required.

    Args:
        preset: gdal preset to use. Defined in `gdal.gdal_preset.py`
        epsg: the EPSG code of the file

    Returns:
        a list of arguments to run `gdal_translate`
    """
    get_log().info("gdal_preset", preset=preset)

    base_command: list[str] = [
        "gdal_translate",
        *BASE_COG,
        "-a_srs",
        f"EPSG:{epsg}",
    ]

    ZSTD_OPTIONS = COMPRESS_ZSTD + ZSTD_OVERVIEWS

    PRESET_OPTIONS: dict[str, list[str]] = {
        CompressionPreset.LZW.value: (SCALE_254_ADD_NO_DATA + COMPRESS_LZW + WEBP_OVERVIEWS),
        CompressionPreset.WEBP.value: (COMPRESS_WEBP_LOSSLESS + WEBP_OVERVIEWS),
        CompressionPreset.RGBNIR_ZSTD.value: ZSTD_OPTIONS,
        CompressionPreset.ZSTD.value: ZSTD_OPTIONS,
        CompressionPreset.DEM_LERC.value: DEM_LERC,
    }

    preset_options = PRESET_OPTIONS.get(preset)
    if preset_options is None:
        raise ValueError(f"Unsupported compression preset: {preset}")

    return base_command + preset_options


def get_cutline_command(cutline: str | None) -> list[str]:
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


def get_build_vrt_command(
    files: list[str],
    output: str = "output.vrt",
    epsg: int = 2193,
    add_alpha: bool = False,
    resolution: list[Decimal] | None = None,
) -> list[str]:
    """Build a VRT from a list of tiff files.

    Args:
        files: list of tiffs to build the vrt from
        output: the name of the VRT generated. Defaults to "output.vrt".
        epsg: the EPSG code (projection) of the source dataset. Defaults to 2193 (NZTM).
        add_alpha: use `-addalpha`. Defaults to False.
        resolution: set user-defined resolution [xres, yres], e.g. [1, 1]. Defaults to None = no scaling.

    Returns:
        The GDAL command to build the VRT.
    """
    # `-allow_projection_difference` is passed to workaround different coordinate system descriptions within the same EPSG
    # Having the same EPSG code for all images is already checked by `linz/argo-tasks` `tile-index-validate`
    gdal_command = ["gdalbuildvrt", "-strict", "-allow_projection_difference", "-a_srs", f"EPSG:{epsg}"]
    if add_alpha:
        gdal_command.append("-addalpha")
    if resolution is not None:
        gdal_command.extend(["-resolution", "user", "-tr"])
        gdal_command.extend(str(xy) for xy in resolution)

    gdal_command.append(output)
    gdal_command += files

    return gdal_command


def get_alpha_command() -> list[str]:
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


def get_relabel_colorinterp_command() -> list[str]:
    """Get a `gdal_edit` command to relabel RGBNIR Band 4 as NIR.

    Returns:
        a list of arguments to run `gdal_edit`
    """

    return ["gdal_edit", "-colorinterp_4", "NIR"]


def get_transform_srs_command(source_epsg: int, target_epsg: int) -> list[str]:
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


def get_thumbnail_command(
    format_: str,
    input_: str,
    output: str,
    xsize: str,
    ysize: str,
    extra_args: list[str] | None = None,
    gdalinfo_data: GdalInfo | None = None,
) -> list[str]:
    """Get a `gdal_translate` command to create thumbnails.

    Args:
        format_: output format.
        input_: input file path.
        output: target output file path.
        xsize: sets the x size of the output file in [%].
        ysize: sets the y size of the output file in [%].
        extra_args: List of extra arguments to add to the gdal command.
        gdalinfo_data: gdalinfo of the `input_` file. Defaults to None.

    Returns:
        a list of arguments to run `gdal_translate`.
    """
    if not extra_args:
        extra_args = []
    command = [
        "gdal_translate",
        "-of",
        format_,
        input_,
        output,
        "-outsize",
        xsize,
        ysize,
    ]
    command.extend(get_gdal_band_offset(input_, gdalinfo_data, None))
    command.extend(extra_args)

    return command


def get_ascii_translate_command() -> list[str]:
    """Get a `translate` command to transform the ascii files to tiff.

    Args:

    Returns:
        a list of arguments to run `gdal_translate`
    """
    return [
        "gdal_translate",
        "-of",
        "GTiff",
        # Ensure all CPUs are used for gdal translate
        "-co",
        "num_threads=all_cpus",
        "-co",
        "COMPRESS=lzw",
    ]


def get_hillshade_command(preset: str) -> list[str]:
    """Get a `gdaldem` command to create a hillshade based on the provided HillshadePreset.

    Args:
        preset: a HillshadePreset

    Returns:
        a `gdaldem` command
    """
    gdal_command: list[str] = [
        "gdaldem",
        "hillshade",
        "-compute_edges",
    ]

    if preset == HillshadePreset.DEFAULT.value:
        gdal_command.extend(["-az", "315", "-alt", "45"])
    elif preset == HillshadePreset.IGOR.value:
        gdal_command.extend(["-igor"])

    return gdal_command


def get_footprint_command(gsd: Decimal, preset: str) -> list[str]:
    gdal_footprint_command: list[str] = [
        "gdal_footprint",
        "-t_srs",
        f"EPSG:{EpsgNumber.WGS_1984.value}",
        "-max_points",
        "unlimited",
        "-lco",
        "COORDINATE_PRECISION=8",
        "-simplify",
        str(get_buffer_distance(gsd)),
    ]
    if preset == CompressionPreset.RGBNIR_ZSTD.value:
        gdal_footprint_command.extend(["-b", "5"])

    return gdal_footprint_command


def get_fillnodata_command() -> list[str]:
    """
    Get a `gdal_fillnodata` command to fill nodata values in a TIFF.
    """
    return ["gdal_fillnodata", "-md", "5", "-b", "1", "-of", "GTiff"]
