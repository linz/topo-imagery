from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from multiprocessing import Pool

from linz_logger import get_log
from tifffile import TiffFile

from scripts.aws.aws_helper import is_s3
from scripts.cli.cli_helper import TileFiles
from scripts.files.file_tiff import FileTiff, FileTiffType
from scripts.files.files_helper import SUFFIX_FOOTPRINT, ContentType, is_tiff
from scripts.files.fs import exists, read, write, write_all, write_sidecars
from scripts.gdal.gdal_bands import get_gdal_band_offset
from scripts.gdal.gdal_commands import (
    get_alpha_command,
    get_build_vrt_command,
    get_cutline_command,
    get_gdal_command,
    get_transform_srs_command,
)
from scripts.gdal.gdal_helper import EpsgNumber, gdal_info, run_gdal
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.capture_area import get_buffer_distance
from scripts.tile.tile_index import Bounds, get_bounds_from_name


@dataclass
class StandardisingConfig:
    """Standardising configuration.
    gdal_preset: gdal preset to use. See `gdal.gdal_preset.py`
    source_epsg: current EPSG code of the source file
    target_epsg: desired EPSG code of the output file
    gsd: expected Ground Sample Distance in meters
    cutline: path to the cutline file. Must be `.fgb` or `.geojson`
    scale_to_resolution: scale TIFFs to the specified x,y resolution. Defaults to None = no scaling.
    """

    gdal_preset: str
    source_epsg: int
    target_epsg: int
    gsd: Decimal
    create_footprints: bool
    cutline: str | None
    scale_to_resolution: list[Decimal] | None = None

    def __post_init__(self) -> None:
        if self.cutline and not self.cutline.endswith((".fgb", ".geojson")):
            raise ValueError(f"Only .fgb or .geojson cutlines are supported: {self.cutline}")
        if self.scale_to_resolution is not None and len(self.scale_to_resolution) != 2:
            raise ValueError(f"scale_to_resolution must be exactly two items [xres, yres]: {self.scale_to_resolution}")


def run_standardising(
    tiles_to_process: list[TileFiles],
    standardising_config: StandardisingConfig,
    concurrency: int,
    gdal_version: str,
    target_output: str = "/tmp/",
) -> list[FileTiff]:
    """Run `standardising()` in parallel (`concurrency`).

    Args:
        tiles_to_process: list of TileFiles (tile name and input files) to standardise
        standardising_config: a StandardisingConfig dictionary, containing
            gdal_preset: gdal preset to use. See `gdal.gdal_preset.py`
            source_epsg: current EPSG code of the source file
            target_epsg: desired EPSG code of the output file
            gsd: expected Ground Sample Distance in meters
            cutline: path to the cutline file. Must be `.fgb` or `.geojson`
            scale_to_resolution: scale TIFFs to the specified x,y resolution. Defaults to None = no scaling.
        concurrency: number of concurrent files to process
        gdal_version: version of GDAL used for standardising
        target_output: output directory path. Defaults to "/tmp/"


    Returns:
        a list of FileTiff wrapper
    """
    # pylint: disable-msg=too-many-arguments
    start_time = time_in_ms()

    get_log().info("standardising_start", gdalVersion=gdal_version, fileCount=len(tiles_to_process))

    with Pool(concurrency) as p:
        standardized_tiffs = [
            entry
            for entry in p.map(
                partial(
                    standardising,
                    config=standardising_config,
                    target_output=target_output,
                ),
                tiles_to_process,
            )
            if entry is not None
        ]
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time, fileCount=len(standardized_tiffs))

    return standardized_tiffs


def create_vrt(
    source_tiffs: list[str], target_path: str, add_alpha: bool = False, resolution: list[Decimal] | None = None
) -> str:
    """Create a VRT from a list of tiffs files

    Args:
        source_tiffs: list of tiffs to create the VRT from
        target_path: path of the generated VRT
        add_alpha: add alpha band to the VRT. Defaults to False.
        resolution: set user-defined resolution [xres, yres], e.g. [1, 1]. Defaults to None = no scaling.

    Returns:
        the path to the VRT created
    """
    # Create the `vrt` file
    vrt_path = os.path.join(target_path, "source.vrt")
    run_gdal(command=get_build_vrt_command(files=source_tiffs, output=vrt_path, add_alpha=add_alpha, resolution=resolution))
    return vrt_path


def standardising(
    files: TileFiles,
    config: StandardisingConfig,
    target_output: str = "/tmp/",
) -> FileTiff | None:
    """Standardise geospatial TIFF files using GDAL.
    Optionally create a footprint sidecar file.

    Args:
        files: a TileFiles named tuple, containing
            output: name of the output tile to be created
            input: list of input files for the creation of the output tile
            includeDerived: whether STAC should include derived_from links
        config: a StandardisingConfig data class, containing
            gdal_preset: gdal preset to use. See `gdal.gdal_preset.py`
            source_epsg: current EPSG code of the source file
            target_epsg: desired EPSG code of the output file
            gsd: expected Ground Sample Distance in meters
            cutline: path to the cutline file. Must be `.fgb` or `.geojson`
            scale_to_resolution: scale TIFFs to the specified x,y resolution. Defaults to None = no scaling.
        target_output: output directory path. Defaults to "/tmp/". Not to be confused with `tmp_path`.

    Raises:
        Exception: if cutline is not a .fgb or .geojson file

    Returns:
        a FileTiff wrapper
    """
    standardised_file_path = os.path.join(target_output, f"{files.output}.tiff")
    tiff = FileTiff(files.inputs, config.gdal_preset, files.includeDerived)
    tiff.set_path_standardised(standardised_file_path)

    # Skip processing if output file already exists
    if exists(standardised_file_path):
        get_log().info("standardised_tiff_already_exists", path=standardised_file_path)
        return tiff

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:

        # Copy source TIFFs and any .prj or .tfw sidecar files to tmp_path
        get_prj_tfw_sidecars(tiff, f"{tmp_path}/source/")
        source_files = write_all(tiff.get_paths_original(), f"{tmp_path}/source/")

        # Determine if VRT needs alpha
        vrt_add_alpha = check_vrt_alpha(source_files)

        # Create base VRT file
        current_working_file = create_vrt(
            [source_file for source_file in source_files if is_tiff(source_file)],
            tmp_path,
            add_alpha=vrt_add_alpha,
            resolution=config.scale_to_resolution,
        )

        # Apply cutline if needed
        current_working_file = apply_cutline(current_working_file, config, tmp_path)

        # Add alpha band to imagery
        current_working_file = add_alpha_to_imagery(current_working_file, tiff, tmp_path)

        # Reproject if needed
        current_working_file = reproject_if_needed(current_working_file, config, tmp_path)

        # Generate output using GDAL
        current_working_file = apply_gdal_transformation(current_working_file, config, tmp_path, tile_name=files.output)

        # Update GDAL info
        tiff.get_gdalinfo(current_working_file)

        # Validate output and create footprints
        if check_tiff_empty(current_working_file):
            return None

        if config.create_footprints:
            temp_footprint = create_footprint(current_working_file, config, tmp_path)
            footprint_file_path = os.path.join(target_output, f"{files.output}{SUFFIX_FOOTPRINT}")
            write(footprint_file_path, read(temp_footprint), content_type=ContentType.GEOJSON.value)

        # Copy the final version of the working / temp file to the desired destination
        write(standardised_file_path, read(current_working_file), content_type=ContentType.GEOTIFF.value)

    return tiff


def get_prj_tfw_sidecars(tiff: FileTiff, target_path: str) -> list[str]:
    """Get any .prj and .tfw sidecar files that have the same basename as the TIFF file."""
    sidecars = [
        f"{os.path.splitext(file_input)[0]}{extension}"
        for extension in [".prj", ".tfw"]
        for file_input in tiff.get_paths_original()
    ]
    write_sidecars(sidecars, target_path)
    return sidecars


def check_vrt_alpha(source_files: list[str]) -> bool:
    """Check if alpha is needed in the VRT."""
    for file in source_files:
        if is_tiff(file):
            bands = gdal_info(file)["bands"]
            if (len(bands) == 4 and bands[3]["colorInterpretation"] == "Alpha") or (
                len(bands) == 1 and bands[0]["colorInterpretation"] == "Gray"
            ):
                return False
    return True


def apply_cutline(input_file: str, config: StandardisingConfig, tmp_path: str) -> str:
    """Apply a cutline to the input VRT if a cutline is provided."""
    if config.cutline:
        if not config.cutline.endswith((".fgb", ".geojson")):
            raise ValueError(f"Only .fgb or .geojson cutlines are supported: {config.cutline}")

        input_cutline_path = config.cutline
        if is_s3(config.cutline):
            input_cutline_path = os.path.join(tmp_path, "cutline" + os.path.splitext(config.cutline)[1])
            write(input_cutline_path, read(config.cutline))

        target_vrt = os.path.join(tmp_path, "cutline.vrt")
        run_gdal(get_cutline_command(input_cutline_path), input_file=input_file, output_file=target_vrt)
        return target_vrt

    return input_file


def add_alpha_to_imagery(input_file: str, tiff: FileTiff, tmp_path: str) -> str:
    """Add alpha band to all imagery for consistency allowing GDAL to run correctly (TDE-804)."""
    if tiff.get_tiff_type() == FileTiffType.IMAGERY:
        target_vrt = os.path.join(tmp_path, "target.vrt")
        get_log().info("Adding alpha band to TIFF", path=input_file, existingTiffBands=gdal_info(input_file)["bands"])
        run_gdal(get_alpha_command(), input_file=input_file, output_file=target_vrt)
        return target_vrt

    return input_file


def reproject_if_needed(input_file: str, config: StandardisingConfig, tmp_path: str) -> str:
    """Reproject the VRT file if source EPSG differs from target EPSG."""
    if config.source_epsg != config.target_epsg:
        target_vrt = os.path.join(tmp_path, "reproject.vrt")
        get_log().info("Reprojecting TIFF", path=input_file, sourceEPSG=config.source_epsg, targetEPSG=config.target_epsg)
        run_gdal(
            get_transform_srs_command(config.source_epsg, config.target_epsg), input_file=input_file, output_file=target_vrt
        )
        return target_vrt
    return input_file


def apply_gdal_transformation(input_file: str, config: StandardisingConfig, tmp_path: str, tile_name: str) -> str:
    """Generate output using GDAL command."""
    target_file = os.path.join(tmp_path, f"{tile_name}.tiff")

    command = get_gdal_command(config.gdal_preset, epsg=int(config.target_epsg))
    command.extend(get_gdal_band_offset(input_file, gdal_info(input_file), config.gdal_preset))

    # Specify the extent to get the right boundaries in case of the tiff got no data on its edges
    output_bounds: Bounds = get_bounds_from_name(tile_name)
    min_x = output_bounds.point.x
    max_y = output_bounds.point.y
    min_y = max_y - output_bounds.size.height
    max_x = min_x + output_bounds.size.width
    command.extend(["-co", f"TARGET_SRS=EPSG:{config.target_epsg}", "-co", f"EXTENT={min_x},{min_y},{max_x},{max_y}"])

    get_log().info("Running GDAL", command=command, input_file=input_file, output_file=target_file)

    # Need GDAL to write to temporary location so no broken files end up in the done folder.
    run_gdal(command, input_file=input_file, output_file=target_file)

    return target_file


def check_tiff_empty(current_working_file: str) -> bool:
    """Check whether the TIFF output is empty."""
    with TiffFile(current_working_file) as file_handle:
        return all(tile_byte_count == 0 for tile_byte_count in file_handle.pages.first.tags["TileByteCounts"].value)


def create_footprint(current_working_file: str, config: StandardisingConfig, tmp_path: str) -> str:
    """Create the footprint from the standardized TIFF."""
    footprint_tmp_path = os.path.join(tmp_path, f"footprint{SUFFIX_FOOTPRINT}")
    run_gdal(
        [
            "gdal_footprint",
            "-t_srs",
            f"EPSG:{EpsgNumber.WGS_1984.value}",
            "-max_points",
            "unlimited",
            "-lco",
            "COORDINATE_PRECISION=8",
            "-simplify",
            str(get_buffer_distance(config.gsd)),
        ],
        current_working_file,
        footprint_tmp_path,
    )
    return footprint_tmp_path
