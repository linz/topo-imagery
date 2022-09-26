import argparse
import json
from typing import List

from linz_logger import get_log

from scripts.cli.cli_helper import format_source
from scripts.files.files_helper import is_json
from scripts.files.fs import write
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem


def update_imagery_collection(files: List[str], collection_path: str) -> None:
    start_time = time_in_ms()
    get_log().info("finalise_stac_collection_imagery_start", collection=collection_path)

    collection = ImageryCollection(path=collection_path)

    for file in files:
        if not is_json(file):
            get_log().trace("create_stac_file_not_tiff_skipped", file=file)
        item = ImageryItem(path=file)
        collection.add_link(href=file)
        collection.update_temporal_extent(item.stac["properties"]["start_datetime"], item.stac["properties"]["end_datetime"])
        collection.update_spatial_extent(item.stac["bbox"])

    write(collection_path, json.dumps(collection.stac).encode("utf-8"))

    get_log().info(
        "update_stac_collection_imagery_complete", collection=collection.stac, source=files, duration=time_in_ms() - start_time
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--collection", dest="collection", help="path to collection.json", required=True)
    arguments = parser.parse_args()

    files = format_source(arguments.source)
    collection_path = arguments.collection

    update_imagery_collection(files, collection_path)


if __name__ == "__main__":
    main()
