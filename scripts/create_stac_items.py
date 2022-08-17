import argparse
import json
import os
from typing import List

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, valid_date
from scripts.files.files_helper import get_file_name_from_path, is_tiff, strip_extension
from scripts.files.fs import write
from scripts.logging.time_helper import time_in_ms
from scripts.stac.item import ImageryItem


def create_items_imagery(files: List[str], date: str) -> None:
    for file in files:
        if not is_tiff(file):
            get_log().trace("create_stac_skipped_file_not_tiff", file=file)
            continue
        filename = strip_extension(get_file_name_from_path(file))
        item = ImageryItem(filename)
        item.create_stac_item(file, date)
        # validate item
        tmp_file_path = os.path.join("/tmp/", f"{filename}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))


def main() -> None:
    start_time = time_in_ms()

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--date", dest="date", help="datetime in format YYYY-MM-DD", type=valid_date, required=True)
    arguments = parser.parse_args()

    files = format_source(arguments.source)

    get_log().info("create_stac_items_start", source=files)
    date = format_date(arguments.date)
    create_items_imagery(files, date)

    get_log().info("create_stac_items_complete", source=files, duration=time_in_ms() - start_time)


if __name__ == "__main__":
    main()
