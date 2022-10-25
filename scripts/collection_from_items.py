import argparse
import json
import os

from boto3 import client
from linz_logger import get_log

from scripts.files.files_helper import is_json
from scripts.files.fs import read, write
from scripts.files.fs_s3 import bucket_name_from_path, prefix_from_path
from scripts.stac.imagery.collection import ImageryCollection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection_id", dest="collection_id", required=True)
    parser.add_argument("--title", dest="title", help="collection title", required=True)
    parser.add_argument("--description", dest="description", help="collection description", required=True)

    arguments = parser.parse_args()

    uri = arguments.uri
    collection = ImageryCollection(
        title=arguments.title, description=arguments.description, collection_id=arguments.collection_id
    )

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    s3_client = client("s3")

    paginator = s3_client.get_paginator("list_objects_v2")
    response_iterator = paginator.paginate(Bucket=bucket_name_from_path(uri), Prefix=prefix_from_path(uri))
    for response in response_iterator:
        for contents_data in response["Contents"]:
            key = contents_data["Key"]
 
            file = os.path.join(f"s3://{bucket_name_from_path(uri)}", key)

            if not is_json(file):
                get_log().info("skipping file as not json", file=file, action="collection_from_items", reason="skip")
                continue

            item_stac = json .loads(read(file).decode("utf-8"))

            if not arguments.collection_id == item_stac["collection"]:
                get_log().info(
                    "skipping file as item.collection does not match collection_id",
                    file=file,
                    action="collection_from_items",
                    reason="skip",
                )
                continue

            collection.add_item(item_stac)
            get_log().info("item added to collection", item=item_stac["id"], file=file)

    valid_item_count = [dictionary["rel"] for dictionary in collection.stac["links"]].count("item")
    get_log().info("All valid items added to collection", valid_item_count=valid_item_count)

    destination = os.path.join(uri, "collection.json")
    write(destination, json.dumps(collection.stac).encode("utf-8"))
    get_log().info("collection written", destination=destination)


if __name__ == "__main__":
    main()
