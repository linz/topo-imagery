import argparse
from functools import partial
import json
from multiprocessing import Pool
import os
from typing import List, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import TileFiles, format_date, format_source, is_argo, valid_date
from scripts.files.fs import exists, write
from scripts.gdal.gdal_helper import get_srs, get_vfs_path, run_gdal
from scripts.gdal.gdal_preset import get_build_vrt_command
from scripts.stac.imagery.create_stac import create_item
from scripts.standardising import run_standardising, TEMP_FOLDER

def bulk_download_tiffs(files: List[TileFiles], concurrency: int) -> List[str]:
    dl_files: List[str] = []
    with Pool(concurrency) as p:
            dl_files = p.map(
                partial(
                    tmp_path=TEMP_FOLDER,
                ),
                files,
            )
            p.close()
            p.join()

def download_tiff_file(tile_files: TileFiles, tmp_path: str) -> str:
    """Download a tiff file and some of its sidecar files if they exist.

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

def get_vrts(source_tiffs: List[str], tilename: Optional[str] = None) -> List[str]:
    # Create the `vrt` file
    if not tilename:

    vrt_file = f"{tilename}.vrt"
    vrt_path = os.path.join(TEMP_FOLDER, vrt_file)
    run_gdal(command=get_build_vrt_command(files=input_tiffs, output=vrt_path))
    return vrt_path

def main() -> None:
    # pylint: disable-msg=too-many-locals
    # TODO: make arguments into reusable code for standardising and standardise-validate
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True, help="Standardised file format. Example: webp")
    parser.add_argument("--source", dest="source", nargs="+", required=True, help="The path to the input tiffs")
    parser.add_argument("--source-epsg", dest="source_epsg", required=True, help="The EPSG code of the source imagery")
    parser.add_argument(
        "--target-epsg",
        dest="target_epsg",
        required=True,
        help="The target EPSG code. If different to source the imagery will be reprojected",
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
    tile_files: List[TileFiles] = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    scale = arguments.scale
    if scale == "None":
        scale = 0
    else:
        scale = int(arguments.scale)
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    

    # Download files
    # If retiling
    # For each tile, download the corresponding source tiffs
    # TODO Do we want the concurrency more than 4?

    bulk_download_tiffs(tile_files, concurrency)

    # Is retiling needed
    output_tilename = format_source(arguments.source)[1]
    source_files = format_source(arguments.source)[0]


    vrts = get_vrts()
    if output_tilename:
        # get vrts
        

    tiff_files = run_standardising(
        vrts,
        output_tilename,
        arguments.preset,
        arguments.cutline,
        concurrency,
        arguments.source_epsg,
        arguments.target_epsg,
        scale,
        arguments.target,
    )

    if len(tiff_files) == 0:
        get_log().info("no_tiff_to_process", action="standardise_validate", reason="skipped")
        return

    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()

    for file in tiff_files:
        stac_item_path = file.get_path_standardised().rsplit(".", 1)[0] + ".json"
        if not exists(stac_item_path):
            file.set_srs(srs)
            file.set_scale(scale)

            # Validate the file
            if not file.validate():
                # If the file is not valid (Non Visual QA errors)
                # Logs the `vsis3` path to use `gdal` on the file directly from `s3`
                # This is to help data analysts to verify the file.
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

            # Create STAC and save in target
            item = create_item(
                file.get_path_standardised(), start_datetime, end_datetime, arguments.collection_id, file.get_gdalinfo()
            )
            write(stac_item_path, json.dumps(item.stac).encode("utf-8"))
            get_log().info("stac_saved", path=stac_item_path)


if __name__ == "__main__":
    main()
