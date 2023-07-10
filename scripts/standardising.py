import os
import tempfile
from functools import partial
from multiprocessing import Pool
from typing import List, Optional

import ulid
from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.cli.cli_helper import TileFiles
from scripts.files.file_tiff import FileTiff
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_bands import get_gdal_band_offset
from scripts.gdal.gdal_helper import get_gdal_version, run_gdal
from scripts.gdal.gdal_preset import get_build_vrt_command, get_cutline_command, get_gdal_command, get_transform_srs_command
from scripts.gdal.gdalinfo import gdal_info
from scripts.logging.time_helper import time_in_ms
from scripts.tile.tile_index import Bounds, get_bounds_from_name


def run_standardising(
    files: List[TileFiles],
    preset: str,
    cutline: Optional[str],
    concurrency: int,
    source_epsg: str,
    target_epsg: str,
    target_output: str = "/tmp/",
) -> List[FileTiff]:
    """Run `standardising()` in parallel (`concurrency`).

    Args:
        files: list of source files to standardise
        preset: gdal preset to use. See `gdal.gdal_preset.py`
        cutline: path to the cutline. Must be `.fgb` or `.geojson`.
        concurrency: number of concurrent files to process
        source_epsg: EPSG code of the source file
        target_epsg: EPSG code of reprojection
        scale: scale on what is based the file to standardise
        target_output: output directory path. Defaults to "/tmp/"

    Returns:
        a list of FileTiff wrapper
    """
    # pylint: disable-msg=too-many-arguments
    start_time = time_in_ms()

    gdal_version = get_gdal_version()
    get_log().info("standardising_start", gdalVersion=gdal_version, fileCount=len(files))

    with Pool(concurrency) as p:
        standardized_tiffs = p.map(
            partial(
                standardising,
                preset=preset,
                source_epsg=source_epsg,
                target_epsg=target_epsg,
                target_output=target_output,
                cutline=cutline,
            ),
            files,
        )
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time, fileCount=len(standardized_tiffs))

    return standardized_tiffs


def download_tiffs(files: List[str], target: str) -> List[str]:
    """Download a tiff file and some of its sidecar files if they exist to the target dir.

    Args:
        files: links source filename to target tilename
        target: target folder to write too

    Returns:
        linked downloaded filename to target tilename

    Example:
    ```
    >>> download_tiff_file(("s3://elevation/SN9457_CE16_10k_0502.tif", "CE16_5000_1003"), "/tmp/")
    ("/tmp/123456.tif", "CE16_5000_1003")
    ```
    """
    downloaded_files: List[str] = []
    for file in files:
        target_file_path = os.path.join(target, str(ulid.ULID()))
        input_file_path = target_file_path + ".tiff"
        get_log().info("download_tiff", path=file, target_path=input_file_path)

        write(input_file_path, read(file))
        downloaded_files.append(input_file_path)

        base_file_path = os.path.splitext(file)[0]
        # Attempt to download sidecar files too
        for ext in [".prj", ".tfw"]:
            try:
                write(target_file_path + ext, read(base_file_path + ext))
                get_log().info("download_tiff_sidecar", path=base_file_path + ext, target_path=target_file_path + ext)

            except:  # pylint: disable-msg=bare-except
                pass

    return downloaded_files


def create_vrt(source_tiffs: List[str], target_path: str, add_alpha: bool = False) -> str:
    # Create the `vrt` file
    vrt_path = os.path.join(target_path, "source.vrt")
    # FIXME throw error if warnings generated
    # gdalbuildvrt does not support heterogeneous band color
    # gdalbuildvrt does not support heterogeneous projection: expected NZGD2000 / New Zealand Transverse
    run_gdal(command=get_build_vrt_command(files=source_tiffs, output=vrt_path, add_alpha=add_alpha))
    return vrt_path


# pylint: disable-msg=too-many-locals
def standardising(
    todo: TileFiles,
    preset: str,
    source_epsg: str,
    target_epsg: str,
    cutline: Optional[str],
    target_output: str = "/tmp/",
) -> FileTiff:
    """Apply transformations using GDAL to the source file.

    Args:
        file: path to the file to standardise
        preset: gdal preset to use. See `gdal.gdal_preset.py`
        source_epsg: EPSG code of the source file
        target_epsg: EPSG code of reprojection
        scale: scale on what is based the file to standardise
        cutline: path to the cutline. Must be `.fgb` or `.geojson`
        target_output: output directory path. Defaults to "/tmp/"

    Raises:
        Exception: if cutline is not a .fgb or .geojson file

    Returns:
        a FileTiff wrapper
    """
    standardized_file_name = todo.output + ".tiff"
    standardized_file_path = os.path.join(target_output, standardized_file_name)
    tiff = FileTiff(todo.input, preset)
    tiff.set_path_standardised(standardized_file_path)

    # Already proccessed can skip processing
    if exists(standardized_file_path):
        get_log().info("standardised_tiff_already_exists", path=standardized_file_path)
        return tiff

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:
        standardized_working_path = os.path.join(tmp_path, standardized_file_name)

        source_tiffs = download_tiffs(todo.input, tmp_path)
        vrt_add_alpha = True

        for file in source_tiffs:
            gdal_data = gdal_info(file, False)
            # gdal_data.epsg # ["epsg"]
            bands = gdal_data["bands"]
            if (len(bands) == 4 and bands[3]["colorInterpretation"] == "Alpha") or (
                len(bands) == 1 and bands[0]["colorInterpretation"] == "Gray"
            ):
                vrt_add_alpha = False
            # TODO ensure bands are the same for all imagery

        # Start from base VRT
        input_file = create_vrt(source_tiffs, tmp_path, add_alpha=vrt_add_alpha)

        # Create base COG from original file
        # base_cog = os.path.join(output_dir, f"{output_tile}_c-LZW.tiff")
        # custom_translate = get_custom_translate(
        #     compression="LZW",
        #     input_file=vrt_path,
        #     output_file=base_cog,
        #     extent_max=Point(max_x, max_y),
        #     extent_min=Point(min_x, min_y),
        #     driver="COG",
        # )
        # run_gdal(command=custom_translate)

        # Apply cutline
        if cutline:
            input_cutline_path = cutline
            if is_s3(cutline):
                if not cutline.endswith((".fgb", ".geojson")):
                    raise Exception(f"Only .fgb or .geojson cutlines are support cutline:{cutline}")
                input_cutline_path = os.path.join(tmp_path, "culine" + os.path.splitext(cutline)[1])
                # Ensure the input cutline is a easy spot for GDAL to read
                write(input_cutline_path, read(cutline))

            target_vrt = os.path.join(tmp_path, "cutline.vrt")
            # TODO: test a cutline with a VRT file
            run_gdal(get_cutline_command(input_cutline_path), input_file=input_file, output_file=target_vrt)
            input_file = target_vrt

        # Reproject tiff if needed
        if source_epsg != target_epsg:
            target_vrt = os.path.join(tmp_path, "reproject.vrt")
            get_log().info("Reprojecting Tiff", path=input_file, sourceEPSG=source_epsg, targetEPSG=target_epsg)
            run_gdal(get_transform_srs_command(source_epsg, target_epsg), input_file=input_file, output_file=target_vrt)
            input_file = target_vrt

        transformed_image_gdalinfo = gdal_info(input_file, False)
        command = get_gdal_command(preset, epsg=target_epsg)
        command.extend(get_gdal_band_offset(input_file, transformed_image_gdalinfo, preset))

        output_bounds: Bounds = get_bounds_from_name(todo.output)
        min_x = output_bounds.point.x
        max_y = output_bounds.point.y
        min_y = max_y - output_bounds.size.height
        max_x = min_x + output_bounds.size.width
        tileExtent = [min_x, min_y, max_x, max_y]
        command.extend(["-co", f"TARGET_SRS=EPSG:{target_epsg}", "-co", f'EXTENT={",".join(str(e) for e in tileExtent)}'])

        # Need GDAL to write to temporary location so no broken files end up in the done folder.
        run_gdal(command, input_file=input_file, output_file=standardized_working_path)

        write(standardized_file_path, read(standardized_working_path))
        return tiff
