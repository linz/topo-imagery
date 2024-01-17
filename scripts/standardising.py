import os
import tempfile
from functools import partial
from multiprocessing import Pool
from typing import List, Optional

from linz_logger import get_log
from tifffile import TiffFile

from scripts.aws.aws_helper import is_s3
from scripts.cli.cli_helper import TileFiles
from scripts.files.file_tiff import FileTiff, FileTiffType
from scripts.files.files_helper import SUFFIX_FOOTPRINT, ContentType, is_tiff
from scripts.files.fs import exists, find_sidecars, read, write, write_all
from scripts.gdal.gdal_bands import get_gdal_band_offset
from scripts.gdal.gdal_helper import get_gdal_version, run_gdal
from scripts.gdal.gdal_preset import (
    get_alpha_command,
    get_build_vrt_command,
    get_cutline_command,
    get_gdal_command,
    get_transform_srs_command,
)
from scripts.gdal.gdalinfo import gdal_info
from scripts.logging.time_helper import time_in_ms
from scripts.tile.tile_index import Bounds, get_bounds_from_name


def run_standardising(
    todo: List[TileFiles],
    preset: str,
    cutline: Optional[str],
    concurrency: int,
    source_epsg: str,
    target_epsg: str,
    target_output: str = "/tmp/",
) -> List[FileTiff]:
    """Run `standardising()` in parallel (`concurrency`).

    Args:
        todo: list of TileFiles (tile name and input files) to standardise
        preset: gdal preset to use. See `gdal.gdal_preset.py`
        cutline: path to the cutline. Must be `.fgb` or `.geojson`
        concurrency: number of concurrent files to process
        source_epsg: EPSG code of the source file
        target_epsg: EPSG code of reprojection
        target_output: output directory path. Defaults to "/tmp/"

    Returns:
        a list of FileTiff wrapper
    """
    # pylint: disable-msg=too-many-arguments
    start_time = time_in_ms()

    gdal_version = get_gdal_version()
    get_log().info("standardising_start", gdalVersion=gdal_version, fileCount=len(todo))

    with Pool(concurrency) as p:
        standardized_tiffs = [
            entry
            for entry in p.map(
                partial(
                    standardising,
                    preset=preset,
                    source_epsg=source_epsg,
                    target_epsg=target_epsg,
                    target_output=target_output,
                    cutline=cutline,
                ),
                todo,
            )
            if entry is not None
        ]
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time, fileCount=len(standardized_tiffs))

    return standardized_tiffs


def create_vrt(source_tiffs: List[str], target_path: str, add_alpha: bool = False) -> str:
    """Create a VRT from a list of tiffs files

    Args:
        source_tiffs: list of tiffs to create the VRT from
        target_path: path of the generated VRT
        add_alpha: add alpha band to the VRT. Defaults to False.

    Returns:
        the path to the VRT created
    """
    # Create the `vrt` file
    vrt_path = os.path.join(target_path, "source.vrt")
    run_gdal(command=get_build_vrt_command(files=source_tiffs, output=vrt_path, add_alpha=add_alpha))
    return vrt_path


# pylint: disable-msg=too-many-locals
# pylint: disable-msg=too-many-statements
def standardising(
    files: TileFiles,
    preset: str,
    source_epsg: str,
    target_epsg: str,
    cutline: Optional[str],
    target_output: str = "/tmp/",
) -> Optional[FileTiff]:
    """Apply transformations using GDAL to the source file and create a footprint sidecar file.

    Args:
        files: paths to the files to standardise
        preset: gdal preset to use. See `gdal.gdal_preset.py`
        source_epsg: EPSG code of the source file
        target_epsg: EPSG code of reprojection
        cutline: path to the cutline. Must be `.fgb` or `.geojson`
        target_output: output directory path. Defaults to "/tmp/"

    Raises:
        Exception: if cutline is not a .fgb or .geojson file

    Returns:
        a FileTiff wrapper
    """
    standardized_file_name = files.output + ".tiff"
    footprint_file_name = files.output + SUFFIX_FOOTPRINT
    standardized_file_path = os.path.join(target_output, standardized_file_name)
    footprint_file_path = os.path.join(target_output, footprint_file_name)
    tiff = FileTiff(files.inputs, preset)
    tiff.set_path_standardised(standardized_file_path)

    # Already proccessed can skip processing
    if exists(standardized_file_path):
        get_log().info("standardised_tiff_already_exists", path=standardized_file_path)
        return tiff

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:
        standardized_working_path = os.path.join(tmp_path, standardized_file_name)
        footprint_tmp_path = os.path.join(tmp_path, footprint_file_name)
        sidecars = find_sidecars(files.inputs, [".prj", ".tfw"])
        source_files = write_all(files.inputs + sidecars, f"{tmp_path}/source/")
        source_tiffs = [file for file in source_files if is_tiff(file)]

        vrt_add_alpha = True

        for file in source_tiffs:
            gdal_data = gdal_info(file)
            bands = gdal_data["bands"]
            if (len(bands) == 4 and bands[3]["colorInterpretation"] == "Alpha") or (
                len(bands) == 1 and bands[0]["colorInterpretation"] == "Gray"
            ):
                vrt_add_alpha = False

        # Start from base VRT
        input_file = create_vrt(source_tiffs, tmp_path, add_alpha=vrt_add_alpha)
        target_vrt = os.path.join(tmp_path, "output.vrt")

        # Apply cutline
        if cutline:
            input_cutline_path = cutline
            if is_s3(cutline):
                if not cutline.endswith((".fgb", ".geojson")):
                    raise Exception(f"Only .fgb or .geojson cutlines are support cutline:{cutline}")
                input_cutline_path = os.path.join(tmp_path, "cutline" + os.path.splitext(cutline)[1])
                # Ensure the input cutline is a easy spot for GDAL to read
                write(input_cutline_path, read(cutline))

            target_vrt = os.path.join(tmp_path, "cutline.vrt")
            run_gdal(get_cutline_command(input_cutline_path), input_file=input_file, output_file=target_vrt)
            input_file = target_vrt
        elif tiff.get_tiff_type() == FileTiffType.IMAGERY:
            target_vrt = os.path.join(tmp_path, "target.vrt")
            # add alpha band to all imagery for consistency allowing GDAL to run correctly (TDE-804)
            run_gdal(get_alpha_command(), input_file=input_file, output_file=target_vrt)
            input_file = target_vrt

        # Reproject tiff if needed
        if source_epsg != target_epsg:
            target_vrt = os.path.join(tmp_path, "reproject.vrt")
            get_log().info("Reprojecting Tiff", path=input_file, sourceEPSG=source_epsg, targetEPSG=target_epsg)
            run_gdal(get_transform_srs_command(source_epsg, target_epsg), input_file=input_file, output_file=target_vrt)
            input_file = target_vrt

        transformed_image_gdalinfo = gdal_info(input_file)
        command = get_gdal_command(preset, epsg=target_epsg)
        command.extend(get_gdal_band_offset(input_file, transformed_image_gdalinfo, preset))

        # Specify the extent to get the right boundaries in case of the tiff got no data on its edges
        output_bounds: Bounds = get_bounds_from_name(files.output)
        min_x = output_bounds.point.x
        max_y = output_bounds.point.y
        min_y = max_y - output_bounds.size.height
        max_x = min_x + output_bounds.size.width
        command.extend(["-co", f"TARGET_SRS=EPSG:{target_epsg}", "-co", f"EXTENT={min_x},{min_y},{max_x},{max_y}"])

        # Need GDAL to write to temporary location so no broken files end up in the done folder.
        run_gdal(command, input_file=input_file, output_file=standardized_working_path)

        with TiffFile(standardized_working_path) as file_handle:
            if any(tile_byte_count != 0 for tile_byte_count in file_handle.pages.first.tags["TileByteCounts"].value):
                # Create footprint GeoJSON
                run_gdal(
                    ["gdal_footprint", "-t_srs", "EPSG:4326"],
                    standardized_working_path,
                    footprint_tmp_path,
                )
                write(standardized_file_path, read(standardized_working_path), content_type=ContentType.GEOTIFF.value)
                write(
                    footprint_file_path,
                    read(footprint_tmp_path),
                    content_type=ContentType.GEOJSON,
                )
                return tiff

        get_log().info("Skipping empty output image", path=input_file, sourceEPSG=source_epsg, targetEPSG=target_epsg)
        return None
