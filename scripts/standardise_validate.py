import argparse
import json
import os
import time
from functools import partial
from multiprocessing import Pool
from typing import Dict, List, Optional, Tuple

import ulid
from linz_logger import get_log

from scripts.cli.cli_helper import TileFiles, format_date, format_source, is_argo, valid_date
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import get_srs, get_vfs_path, run_gdal
from scripts.gdal.gdal_preset import get_build_vrt_command
from scripts.stac.imagery.create_stac import create_item
from scripts.standardising import run_standardising


def bulk_download_tiffs(files: List[TileFiles], concurrency: int) -> Dict[str, List[str]]:
    # need to identify each input files to its output tile name
    #     [
    #   {
    #     "output": "CE16_5000_1001",
    #     "input": [
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_01231.tif"
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_04355.tif"
    #     ]
    #   },
    #   {
    #     "output": "CE16_5000_1003",
    #     "input": [
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0502.tif",
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0503.tif"
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0504.tif",
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0505.tif"
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0506.tif",
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0507.tif"
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0508.tif",
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0509.tif"
    #     ]
    #   },
    # ]

    #     "to_download": [
    #       ("s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_01231.tif", tilename)
    #       ("s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_04355.tif", tilename)
    #     ]

    #     "downloaded": [
    #       ("/tmp/SN9457_CE16_10k_01231.tif", tilename)
    #       ("/tmp/SN9457_CE16_10k_04355.tif", tilename)
    #     ]

    # recreate with downloaded paths
    #   {
    #     "output": "CE16_5000_1001",
    #     "input": [
    #       "/tmp/SN9457/TILES/SN9457_CE16_10k_01231.tif"
    #       "/tmp/SN9457_CE16_10k_04355.tif"
    #     ]
    #   },

    tile_list: List[Tuple[str, str]] = []

    for tile in files:
        for input in tile.input:
            tile_list.append((input, tile.output))

    with Pool(concurrency) as p:
        download_tiffs = p.map(
            partial(
                download_tiff_file,
                tmp_path=TEMP_FOLDER,
            ),
            tile_list,
        )
        p.close()
        p.join()

    local_list: Dict[str, List[str]] = {}
    for output in download_tiffs:
        filepath = output[0]
        tilename = output[1]
        if local_list.get(tilename):
            local_list[tilename].append(filepath)
        else:
            local_list[tilename] = [filepath]
    print(local_list)
    return local_list


def download_tiff_file(file: Tuple[str, str], tmp_path: str) -> Tuple[str, str]:
    """Download a tiff file and some of its sidecar files if they exist.

    Args:
        file: links source filename to target tilename
        tmp_path: target folder to write too

    Returns:
        linked downloaded filename to target tilename

    Example:
    ```
    >>> download_tiff_file(("s3://elevation/SN9457_CE16_10k_0502.tif", "CE16_5000_1003"), "/tmp/")
    ("/tmp/123456.tif", "CE16_5000_1003")
    ```
    """
    target_file_path = os.path.join(tmp_path, str(ulid.ULID()))
    input_file_path = target_file_path + ".tiff"
    get_log().info("download_tiff", path=file[0], target_path=input_file_path)

    write(input_file_path, read(file[0]))

    base_file_path = os.path.splitext(file[0])[0]
    # Attempt to download sidecar files too
    for ext in [".prj", ".tfw"]:
        try:
            write(target_file_path + ext, read(base_file_path + ext))
            get_log().info("download_tiff_sidecar", path=base_file_path + ext, target_path=target_file_path + ext)

        except:  # pylint: disable-msg=bare-except
            pass

    return (input_file_path, file[1])


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
    # parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    # parser.add_argument(
    #     "--start-datetime", dest="start_datetime", help="Start datetime in format YYYY-MM-DD", type=valid_date, required=True
    # )
    # parser.add_argument(
    #     "--end-datetime", dest="end_datetime", help="End datetime in format YYYY-MM-DD", type=valid_date, required=True
    # )
    parser.add_argument("--target", dest="target", help="Target output", required=True)
    arguments = parser.parse_args()
    tile_files: List[TileFiles] = format_source(arguments.source)
    # start_datetime = format_date(arguments.start_datetime)
    # end_datetime = format_date(arguments.end_datetime)
    # scale = arguments.scale
    # if scale == "None":
    #     scale = 0
    # else:
    #     scale = int(arguments.scale)
    concurrency: int = 2
    if is_argo():
        concurrency = 4

    #     [
    #   {
    #     "output": "CE16_5000_1001",
    #     "input": [
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0501.tif"
    #     ]
    #   },
    #   {
    #     "output": "CE16_5000_1003",
    #     "input": [
    #       "s3://linz-topographic-upload/skyvuw/SN9457/TILES/SN9457_CE16_10k_0502.tif"
    #     ]
    #   },
    # ]vrts = get_vrts()

    #     [
    #   {
    #     "output": "CE16_5000_1001",
    #     "input": [
    #       "/tmp/SN9457_CE16_10k_0501.tif"
    #     ]
    #   },
    #   {
    #     "output": "CE16_5000_1003",
    #     "input": [
    #       "/tmp/SN9457_CE16_10k_0502.tif"
    #     ]
    #   },
    # ]

    # # Download files
    # # For each tile, download the corresponding source tiffs
    # # TODO Do we want the concurrency more than 4?
    # file_list = bulk_download_tiffs(tile_files, concurrency)

    # # Create VRTs
    # vrt_to_standardise: List[str] = []
    # for tilename, files in file_list.items():
    #     # TODO remove debug
    #     print(f"Create VRTs for tile {tilename} containing files {files}")
    #     vrt_to_standardise.append(create_vrt(files, tilename))
    # # TODO remove debug
    # print(f"VRTs to process: {vrt_to_standardise}")

    tiff_files = run_standardising(
        tile_files,
        arguments.preset,
        arguments.cutline,
        concurrency,
        arguments.source_epsg,
        arguments.target_epsg,
        arguments.target,
    )

    # if len(tiff_files) == 0:
    #     get_log().info("no_tiff_to_process", action="standardise_validate", reason="skipped")
    #     return

    # # SRS needed for FileCheck (non visual QA)
    # srs = get_srs()

    # for file in tiff_files:
    #     stac_item_path = file.get_path_standardised().rsplit(".", 1)[0] + ".json"
    #     if not exists(stac_item_path):
    #         file.set_srs(srs)
    #         file.set_scale(scale)

    #         # Validate the file
    #         if not file.validate():
    #             # If the file is not valid (Non Visual QA errors)
    #             # Logs the `vsis3` path to use `gdal` on the file directly from `s3`
    #             # This is to help data analysts to verify the file.
    #             original_path = file.get_path_original()
    #             standardised_path = file.get_path_standardised()
    #             env_argo_template = os.environ.get("ARGO_TEMPLATE")
    #             if env_argo_template:
    #                 argo_template = json.loads(env_argo_template)
    #                 s3_information = argo_template["archiveLocation"]["s3"]
    #                 standardised_path = os.path.join(
    #                     "/vsis3",
    #                     s3_information["bucket"],
    #                     s3_information["key"],
    #                     *file.get_path_standardised().split("/"),
    #                 )
    #                 original_path = get_vfs_path(file.get_path_original())
    #             get_log().info(
    #                 "non_visual_qa_errors",
    #                 originalPath=original_path,
    #                 standardisedPath=standardised_path,
    #                 errors=file.get_errors(),
    #             )
    #         else:
    #             get_log().info("non_visual_qa_passed", path=file.get_path_original())

    #         # Create STAC and save in target
    #         item = create_item(
    #             file.get_path_standardised(), start_datetime, end_datetime, arguments.collection_id, file.get_gdalinfo()
    #         )
    #         write(stac_item_path, json.dumps(item.stac).encode("utf-8"))
    #         get_log().info("stac_saved", path=stac_item_path)


if __name__ == "__main__":
    main()
