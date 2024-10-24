import argparse
import json
from argparse import Namespace
from typing import List

from ulid import ULID

from scripts.collection_from_items import s3_uri
from scripts.files import fs_s3


def parse_args(args: List[str] | None) -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--odr-url",
        dest="odr_url",
        help="Open Data Registry collection.json URL of existing dataset",
        required=False,
        type=s3_uri,
    )
    return parser.parse_args(args)


def main(args: List[str] | None = None) -> None:
    arguments = parse_args(args)

    if odr_url := arguments.odr_url:
        odr_collection_bytes = fs_s3.read(odr_url).decode("utf-8")
        odr_collection = json.loads(odr_collection_bytes)
        collection_id = odr_collection["id"]

        if linz_slug := odr_collection["linz:slug"]:
            with open("/tmp/linz_slug", "w", encoding="utf-8") as slug_file:
                slug_file.write(linz_slug)
    else:
        collection_id = str(ULID())

    with open("/tmp/collection-id", "w", encoding="utf-8") as collection_id_file:
        collection_id_file.write(collection_id)


if __name__ == "__main__":
    main()
