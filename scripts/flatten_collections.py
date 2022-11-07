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
    parser.add_argument("--collection_id", dest="collection_id", required=True)
    parser.add_argument("--destination", dest="destination", required=True)

    arguments = parser.parse_args()

    source = format_source(arguments.source)

    collection = None

    for file in source:

        if not is_json(file):
            get_log().info("skipping file as not json", file=file, action="merge_collection", reason="skip")
            continue

        if not file.endswith("/collection.json"):
            get_log().info("skipping file as not collection.json", file=file, action="merge_collection", reason="skip")
            continue

        partial_stac = json.loads(read(file).decode("utf-8"))

        if not arguments.collection_id == partial_stac["id"]:
            get_log().info(
                "skipping file as file collection.id does not match input ulid",
                file=file,
                action="merge_collections",
                reason="skip",
            )
            continue

        if not collection:
            collection = ImageryCollection(
                title=partial_stac["title"], description=partial_stac["description"], collection_id=arguments.collection_id
            )
            collection.stac = partial_stac
            continue

        # merge links
        for link in partial_stac["links"]:
            if link["rel"] != "self":
                collection.add_link(href=link["href"], rel=link["rel"], file_type=link["type"])

        collection.update_spatial_extent(partial_stac["extent"]["spatial"]["bbox"][0])
        start_datetime = min(partial_stac["extent"]["temporal"]["interval"][0][0], partial_stac["extent"]["temporal"]["interval"][0][1])
        end_datetime = max(partial_stac["extent"]["temporal"]["interval"][0][0], partial_stac["extent"]["temporal"]["interval"][0][1])
        collection.update_temporal_extent(start_datetime, end_datetime)

    if collection:
        write(os.path.join(arguments.destination, "collection.json"), json.dumps(collection.stac).encode("utf-8"))


if __name__ == "__main__":
    main()
