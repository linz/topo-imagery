import argparse
import json
import os

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac import create_item
from scripts.files.files_helper import is_tiff
from scripts.files.fs import write
from scripts.gdal.gdalinfo import gdal_info
from scripts.non_visual_qa import get_srs, qa_file
from scripts.standardising import start_standardising


def main() -> None:

    concurrency: int = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--collection_id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )

    arguments = parser.parse_args()

    source = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    collection_id = arguments.collection_id

    if is_argo():
        concurrency = 4

    standardised_files = start_standardising(source, arguments.preset, concurrency)
    if not standardised_files:
        get_log().info("Process skipped because no file has been standardised", action="standardise_validate", reason="skip")
        return
    srs = get_srs()

    for file in standardised_files:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue
        gdalinfo_result = gdal_info(file)
        qa_file(file, srs, gdalinfo_result)
        item = create_item(file, start_datetime, end_datetime, collection_id, gdalinfo_result)

        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac item written to tmp", location=tmp_file_path)


if __name__ == "__main__":
    main()
