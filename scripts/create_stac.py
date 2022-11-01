import argparse
import json
import os
from typing import Any, Dict, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, valid_date
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.files.fs import write
from scripts.files.geotiff import get_extents
from scripts.gdal.gdalinfo import gdal_info
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--collection_id", dest="collection_id", help="Unique id for collection", required=False)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--title", dest="title", help="collection title", required=True)
    parser.add_argument("--description", dest="description", help="collection description", required=True)

    arguments = parser.parse_args()

    source = format_source(arguments.source)
    title = arguments.title
    description = arguments.description
    collection_id = arguments.collection_id
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)

    if arguments.collection_id:
        collection = ImageryCollection(title=title, description=description, collection_id=collection_id)
    else:
        collection = ImageryCollection(title=title, description=description)

    for file in source:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue
        gdalinfo_result = gdal_info(file)
        item = create_item(file, start_datetime, end_datetime, collection_id, gdalinfo_result)
        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac item written to tmp", location=tmp_file_path)

        collection.add_item(item.stac)

    tmp_file_path = os.path.join("/tmp/", "collection.json")
    write(tmp_file_path, json.dumps(collection.stac).encode("utf-8"))


def create_item(
    file: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdalinfo_result: Optional[Dict[Any, Any]] = None,
) -> ImageryItem:
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file)
    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection_id)

    get_log().info("imagery stac item created", file=file)
    return item


if __name__ == "__main__":
    main()
