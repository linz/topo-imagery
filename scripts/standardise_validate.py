import argparse
import json
import os
from typing import List, Tuple

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac import create_item
from scripts.files.file_tiff import FileTiff
from scripts.files.files_helper import get_file_name_from_path, is_tiff, is_vrt
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import get_srs, get_vfs_path
from scripts.gdal.gdalinfo import gdal_info, get_origin
from scripts.standardising import run_standardising
from scripts.tile.tile_index import get_tile_name


def get_processed_tiffs(source: List[str], target: str, scale: int) -> Tuple[List[str], List[FileTiff]]:
    """By checking the target path, return a list of the source path that have been processed
    and a list of tiff that haven't a STAC file associated.

    Args:
        source: the list of image source path
        target: the target location for the processed output (tiff and stac)
        scale: the scale of the dataset

    Returns:
        A tuple containing processed source path and a list of tiff with no stac
    """
    processed_tiffs: List[str] = []
    no_stac: List[FileTiff] = []
    for path in source:
        if is_tiff(path) or is_vrt(path):
            # gdalinfo the original file
            gdalinfo = gdal_info(path)
            origin = get_origin(gdalinfo)
            tile_name = get_tile_name(origin, scale)
            prefix = os.path.join(target, tile_name)
            target_path_stac = prefix + ".json"
            target_path_tiff = prefix + ".tiff"
            # STAC item json file name
            if exists(target_path_stac):
                # STAC exists, consider the TIFF exists too
                processed_tiffs.append(path)
                continue

            if exists(target_path_tiff):
                # TIFF has been processed in previous run
                processed_tiffs.append(path)
                # TIFF exists but not STAC, needs to validate and create the STAC
                tiff = FileTiff(path)
                tiff.set_path_standardised(target_path_tiff)
                no_stac.append(tiff)
    return processed_tiffs, no_stac


def main() -> None:
    # pylint: disable-msg=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True, help="Standardised file format. Example: webp")
    parser.add_argument("--source", dest="source", nargs="+", required=True, help="The path to the input tiffs")
    parser.add_argument("--source-epsg", dest="source_epsg", required=True, help="The EPSP code of the source imagery")
    parser.add_argument(
        "--target-epsg",
        dest="target_epsg",
        required=True,
        help="The target EPSP code. If different to source the imagery will be reprojected",
    )
    parser.add_argument("--cutline", dest="cutline", help="Optional cutline to cut imagery to", required=False, nargs="?")
    parser.add_argument("--scale", dest="scale", help="Tile grid scale to align output tile to", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime", dest="start_datetime", help="Start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end-datetime", dest="end_datetime", help="End datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--target", dest="target", help="Target output", required=True)
    arguments = parser.parse_args()
    source = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    # The target exists, consider this is a resumed workflow
    is_resuming = exists(arguments.target)
    missing_stac_tiffs: List[FileTiff] = []
    if is_resuming:
        # pylint: disable=unbalanced-tuple-unpacking
        processed_tiffs, missing_stac_tiffs = get_processed_tiffs(source, arguments.target, int(arguments.scale))

        for already_processed in processed_tiffs:
            get_log().info("tiff_already_processed", path=already_processed)
            source.remove(already_processed)
    else:
        if not is_argo():
            os.makedirs(arguments.target)

    # Standardize the tiffs
    tiff_files: List[FileTiff] = []
    if len(source):
        tiff_files = run_standardising(
            source, arguments.preset, arguments.cutline, concurrency, arguments.source_epsg, arguments.target_epsg
        )
    # Add TIFFS having no STAC (item.json)
    tiff_files.extend(missing_stac_tiffs)

    if len(tiff_files) == 0:
        get_log().info("no_tiff_to_process", action="standardise_validate", reason="skipped")
        return

    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()

    for file in tiff_files:
        file.set_srs(srs)
        scale = arguments.scale
        if scale == "None":
            file.set_scale(0)
        else:
            file.set_scale(int(scale))

        # Validate the file
        if not file.validate():
            original_path = file.get_path_original()
            standardised_path = file.get_path_standardised()
            env_argo_template = os.environ.get("ARGO_TEMPLATE")
            if env_argo_template:
                argo_template = json.loads(env_argo_template)
                s3_information = argo_template["archiveLocation"]["s3"]
                standardised_path = os.path.join(
                    "/vsis3",
                    s3_information["bucket"],
                    s3_information["key"],
                    *file.get_path_standardised().split("/"),
                )
                original_path = get_vfs_path(file.get_path_original())
            get_log().info(
                "non_visual_qa_errors",
                originalPath=original_path,
                standardisedPath=standardised_path,
                errors=file.get_errors(),
            )
        else:
            get_log().info("non_visual_qa_passed", path=file.get_path_original())

        # Move TIFF to target
        target_tiff = os.path.join(arguments.target, get_file_name_from_path(file.get_path_standardised())) + ".tiff"
        if file.get_path_standardised() != target_tiff:
            write(target_tiff, read(file.get_path_standardised()))
            get_log().info("file_moved", origin=file.get_path_standardised(), destination=target_tiff)
        # Create STAC and save in target
        item = create_item(target_tiff, start_datetime, end_datetime, arguments.collection_id, file.get_gdalinfo())
        tmp_file_path = os.path.join(arguments.target, f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac_saved", path=tmp_file_path)


if __name__ == "__main__":
    main()
