import argparse
import json
import os

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac import create_item
from scripts.files.file_check import FileCheck
from scripts.files.files_helper import is_tiff
from scripts.files.fs import write
from scripts.gdal.gdal_helper import get_srs
from scripts.standardising import start_standardising


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--cutline", dest="cutline", help="Optional cutline to cut imagery to", required=True)

    parser.add_argument("--scale", dest="scale", help="Tile grid scale to align output tile to", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end-datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    arguments = parser.parse_args()

    source = format_source(arguments.source)
    scale = int(arguments.scale)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    collection_id = arguments.collection_id
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    standardised_files = start_standardising(source, arguments.preset, arguments.cutline, concurrency)
    if not standardised_files:
        get_log().info("Process skipped because no file has been standardised", action="standardise_validate", reason="skip")
        return
    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()
    for file in standardised_files:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue

        # Validate the file
        file_check = FileCheck(file, scale, srs)
        if not file_check.validate():
            get_log().info("non_visual_qa_errors", file=file_check.path, errors=file_check.errors)
        else:
            get_log().info("non_visual_qa_passed", file=file_check.path)
        # Get the new path if the file has been renamed
        file = file_check.path
        # Create STAC
        gdalinfo = file_check.get_gdalinfo()
        item = create_item(file, start_datetime, end_datetime, collection_id, gdalinfo)
        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac item written to tmp", location=tmp_file_path)


if __name__ == "__main__":
    main()
