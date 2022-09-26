import argparse
import json
import os
from typing import Any, Dict, List, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, valid_date
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.files.fs import write
from scripts.gdal.gdalinfo import gdal_info
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.util.geotiff import get_extents


def create_imagery_items(files: List[str], start_datetime: str, end_datetime: str, collection_path: str) -> None:
    start_time = time_in_ms()

    get_log().info("read collection object", source=collection_path)
    collection = ImageryCollection(path=collection_path)

    get_log().info("create_stac_items_imagery_start", source=files)

    for file in files:
        if not is_tiff(file):
            get_log().trace("create_stac_file_not_tiff_skipped", file=file)
            continue

        create_item(file, start_datetime, end_datetime, collection)

    get_log().info("create_stac_items_imagery_complete", source=files, duration=time_in_ms() - start_time)


def create_item(
    file: str,
    start_datetime: str,
    end_datetime: str,
    collection: ImageryCollection,
    gdalinfo_result: Optional[Dict[Any, Any]] = None,
) -> None:
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file)
    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection)

    tmp_file_path = os.path.join("/tmp/", f"{id_}.json")
    write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
    get_log().info("imagery_stac_item_created", file=file)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--collection", dest="collection", help="path to collection.json", required=True)
    arguments = parser.parse_args()

    source = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    collection_path = arguments.collection

    create_imagery_items(source, start_datetime, end_datetime, collection_path)


if __name__ == "__main__":
    main()
