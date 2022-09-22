import argparse
import json
import os

from linz_logger import get_log

from scripts.files.fs import write
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection


def initialise_imagery_collection(title: str, description: str) -> None:
    start_time = time_in_ms()
    get_log().info("finalise_stac_collection_imagery_start", title=title, description=description)

    collection = ImageryCollection(title=title, description=description)

    tmp_file_path = os.path.join("/tmp/", "collection.json")
    write(tmp_file_path, json.dumps(collection.stac).encode("utf-8"))

    get_log().info("create_stac_collection_imagery_complete", title=title, duration=time_in_ms() - start_time)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", dest="title", required=True)
    parser.add_argument("--description", dest="description", required=True)

    arguments = parser.parse_args()

    title = arguments.title
    description = arguments.description

    initialise_imagery_collection(title, description)


if __name__ == "__main__":
    main()
