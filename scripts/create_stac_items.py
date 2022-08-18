import argparse
import json
import os
from typing import List

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, valid_date
from scripts.files.files_helper import get_file_name_from_path, is_tiff, strip_extension
from scripts.files.fs import write
from scripts.logging.time_helper import time_in_ms
from scripts.stac import imagery_stac
from scripts.stac.util.checksum import multihash_as_hex
from scripts.stac.util.geotiff import get_extents


def create_imagery_items(files: List[str], date: str) -> None:
    for path in files:
        if not is_tiff(path):
            get_log().trace("create_stac_skipped_file_not_tiff", file=path)
            continue

        id_ = strip_extension(get_file_name_from_path(path))
        geometry, bbox = get_extents(path)
        checksum = multihash_as_hex(path)

        stac = imagery_stac.create_item(id_, path, date, geometry, bbox, checksum)

        tmp_file_path = os.path.join("/tmp/", f"{id_}.json")
        write(tmp_file_path, json.dumps(stac).encode("utf-8"))

        get_log().info("Imagery Stac Item Created", tiff_path=path, stac=stac)


def main() -> None:
    start_time = time_in_ms()

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--date", dest="date", help="datetime in format YYYY-MM-DD", type=valid_date, required=True)
    arguments = parser.parse_args()

    files = format_source(arguments.source)
    date = format_date(arguments.date)

    get_log().info("create_stac_items_start", source=files)

    create_imagery_items(files, date)

    get_log().info("create_stac_items_complete", source=files, duration=time_in_ms() - start_time)


if __name__ == "__main__":
    main()
