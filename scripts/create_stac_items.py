import argparse
import json
import os
from typing import List

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, valid_date
from scripts.files.files_helper import get_file_name_from_path, is_tiff, strip_extension
from scripts.files.fs import write
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery_stac import create_imagery_stac_item


def create_imagery_items(files: List[str], start_datetime: str, end_datetime: str) -> None:
    start_time = time_in_ms()
    get_log().info("create_stac_items_start", source=files)

    for path in files:
        if not is_tiff(path):
            get_log().trace("create_stac_skipped_file_not_tiff", file=path)
            continue

        id_ = strip_extension(get_file_name_from_path(path))
        stac = create_imagery_stac_item(id_, path, start_datetime, end_datetime)

        tmp_file_path = os.path.join("/tmp/", f"{id_}.json")
        write(tmp_file_path, json.dumps(stac).encode("utf-8"))

        get_log().trace("Imagery Stac Item Created", tiff_path=path, stac=stac)

    get_log().info("create_stac_items_complete", source=files, duration=time_in_ms() - start_time)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    arguments = parser.parse_args()

    files = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)

    create_imagery_items(files, start_datetime, end_datetime)


if __name__ == "__main__":
    main()
