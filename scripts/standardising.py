import argparse
import os
import tempfile
from functools import partial
from multiprocessing import Pool
from typing import List, Optional

import ulid
from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.cli.cli_helper import format_source, is_argo
from scripts.files.file_tiff import FileTiff
from scripts.files.files_helper import is_tiff, is_vrt
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_bands import get_gdal_band_offset, get_gdal_band_type
from scripts.gdal.gdal_helper import get_gdal_version, run_gdal
from scripts.gdal.gdal_preset import get_alpha_command, get_cutline_command, get_gdal_command, get_transform_srs_command
from scripts.gdal.gdalinfo import gdal_info, get_origin
from scripts.logging.time_helper import time_in_ms
from scripts.tile.tile_index import get_tile_name


def run_standardising(
    files: List[str],
    preset: str,
    cutline: Optional[str],
    concurrency: int,
    source_epsg: str,
    target_epsg: str,
    scale: int,
    target_output: Optional[str] = None,
) -> List[FileTiff]:
    # pylint: disable-msg=too-many-arguments
    start_time = time_in_ms()
    actual_tiffs = []
    standardized_tiffs: List[FileTiff] = []

    for file in files:
        if is_tiff(file) or is_vrt(file):
            actual_tiffs.append(file)
        else:
            get_log().info("standardising_file_not_tiff_skipped", file=file)

    gdal_version = get_gdal_version()
    get_log().info("standardising_start", gdalVersion=gdal_version, fileCount=len(actual_tiffs))

    with Pool(concurrency) as p:
        standardized_tiffs = p.map(
            partial(
                standardising,
                preset=preset,
                source_epsg=source_epsg,
                target_epsg=target_epsg,
                scale=scale,
                target_output=target_output,
                cutline=cutline,
            ),
            actual_tiffs,
        )
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time, fileCount=len(standardized_tiffs))

    return standardized_tiffs


def download_tiff_file(input_file: str, tmp_path: str) -> str:
    """Download a tiff file and some of its sidecar files if they exist

    Args:
        input_file: file to download
        tmp_path: target folder to write too

    Returns:
        location of the downloaded tiff
    """
    target_file_path = os.path.join(tmp_path, str(ulid.ULID()))
    input_file_path = target_file_path + ".tiff"
    get_log().info("download_tiff", path=input_file, target_path=input_file_path)

    write(input_file_path, read(input_file))

    base_file_path = os.path.splitext(input_file)[0]
    # Attempt to download sidecar files too
    for ext in [".prj", ".tfw"]:
        try:
            write(target_file_path + ext, read(base_file_path + ext))
            get_log().info("download_tiff_sidecar", path=base_file_path + ext, target_path=target_file_path + ext)

        except:  # pylint: disable-msg=bare-except
            pass

    return input_file_path


# pylint: disable-msg=too-many-locals
def standardising(
    file: str,
    preset: str,
    source_epsg: str,
    target_epsg: str,
    scale: int,
    cutline: Optional[str],
    target_output: str = "/tmp/",
) -> FileTiff:
    get_log().info("standardising", path=file)
    original_gdalinfo = gdal_info(file, False)
    origin = get_origin(original_gdalinfo)
    tile_name = get_tile_name(origin, scale)
    standardized_file_name = f"{tile_name}.tiff"
    standardized_file_path = os.path.join(target_output, standardized_file_name)
    tiff = FileTiff(file)

    if not exists(standardized_file_path):
        with tempfile.TemporaryDirectory() as tmp_path:
            standardized_working_path = os.path.join(tmp_path, standardized_file_name)
            input_file = file

            # Ensure the remote file can be read locally, having multiple s3 paths with different credentials
            # makes it hard for GDAL to do its thing
            if is_s3(input_file):
                input_file = download_tiff_file(input_file, tmp_path)

            if cutline:
                input_cutline_path = cutline
                if is_s3(cutline):
                    if not cutline.endswith((".fgb", ".geojson")):
                        raise Exception(f"Only .fgb or .geojson cutlines are support cutline:{cutline}")
                    input_cutline_path = os.path.join(tmp_path, str(ulid.ULID()) + os.path.splitext(cutline)[1])
                    # Ensure the input cutline is a easy spot for GDAL to read
                    write(input_cutline_path, read(cutline))

                target_vrt = os.path.join(tmp_path, str(ulid.ULID()) + ".vrt")
                run_gdal(get_cutline_command(input_cutline_path), input_file=input_file, output_file=target_vrt)
                input_file = target_vrt

            else:
                if tiff.is_no_data(original_gdalinfo):
                    target_vrt = os.path.join(tmp_path, str(ulid.ULID()) + ".vrt")
                    run_gdal(get_alpha_command(), input_file=input_file, output_file=target_vrt)
                    input_file = target_vrt

            if source_epsg != target_epsg:
                target_vrt = os.path.join(tmp_path, str(ulid.ULID()) + ".vrt")
                get_log().info("Reprojecting Tiff", path=input_file, sourceEPSG=source_epsg, targetEPSG=target_epsg)
                run_gdal(get_transform_srs_command(source_epsg, target_epsg), input_file=input_file, output_file=target_vrt)
                input_file = target_vrt

            # gdalinfo to get band offset and band type
            transformed_image_gdalinfo = gdal_info(input_file, False)
            command = get_gdal_command(
                preset, epsg=target_epsg, convert_from=get_gdal_band_type(input_file, transformed_image_gdalinfo)
            )
            command.extend(get_gdal_band_offset(input_file, transformed_image_gdalinfo))
            run_gdal(command, input_file=input_file, output_file=standardized_working_path)

            write(standardized_file_path, read(standardized_working_path))
    else:
        get_log().info("standardised_tiff_already_exists", path=standardized_file_path)

    tiff.set_path_standardised(standardized_file_path)
    return tiff


def main() -> None:
    concurrency: int = 1
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--cutline", dest="cutline", required=False)
    parser.add_argument("--source-epsg", dest="source_epsg", required=True)
    parser.add_argument("--target-epsg", dest="target_epsg", required=True)
    parser.add_argument("--scale", dest="scale", required=True)
    arguments = parser.parse_args()
    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    run_standardising(
        source,
        arguments.preset,
        arguments.cutline,
        concurrency,
        arguments.source_epsg,
        arguments.target_epsg,
        int(arguments.scale),
    )


if __name__ == "__main__":
    main()
