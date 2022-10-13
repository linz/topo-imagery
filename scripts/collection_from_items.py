import argparse
import json
import os

from linz_logger import get_log

from scripts.cli.cli_helper import format_source
from scripts.files.files_helper import is_json
from scripts.files.fs import read, write
from scripts.stac.imagery.collection import ImageryCollection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--title", dest="title", help="collection title", required=True)
    parser.add_argument("--description", dest="description", help="collection description", required=True)
    parser.add_argument("--destination", dest="destination", help="path collection.json should be written to", required=True)

    arguments = parser.parse_args()

    source = format_source(arguments.source)

    collection = ImageryCollection(title=arguments.title, description=arguments.description)
    collection.stac["id"] = None

    for file in source:
        if not is_json(file):
            get_log().trace("skipping file as not json", file=file, action="collection_from_items", reason="skip")
            continue
        
        item_stac = json.loads(read(file).decode("utf-8"))

        if not collection.stac["id"]:
            collection.stac["id"] = item_stac["collection"]
            get_log().info(f"collection id {collection.stac['id']}")

        elif not collection.stac["id"] == item_stac["collection"]:
            get_log().trace("skipping file as item.collection does not match collection.id", file=file, action="collection_from_items", reason="skip")
            continue

        collection.add_item(item_stac)


    tmp_file_path = os.path.join(arguments.destination, "collection.json")
    write(tmp_file_path, json.dumps(collection.stac).encode("utf-8"))


if __name__ == "__main__":
    main()
