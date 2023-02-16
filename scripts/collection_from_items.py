import argparse
import json
import os
from typing import List

from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import parse_list
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_json_in_uri
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.provider import Provider, ProviderRole


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", required=True)
    parser.add_argument("--title", dest="title", help="collection title", required=True)
    parser.add_argument("--description", dest="description", help="collection description", required=True)
    parser.add_argument("--producer", dest="producer", help="imagery producer", required=True)
    parser.add_argument("--licensor", dest="licensor", help="imagery licensor")
    parser.add_argument("--licensor-list", dest="licensor_list", help="imagery licensor list")
    parser.add_argument(
        "--concurrency", dest="concurrency", help="The number of files to limit concurrent reads", required=True, type=int
    )

    arguments = parser.parse_args()
    uri = arguments.uri
    licensors: List[str] = parse_list(arguments.licensor_list)
    if len(licensors) <= 1:
        licensors = [arguments.licensor]

    providers: List[Provider] = []
    for licensor_name in licensors:
        providers.append({"name": licensor_name, "roles": [ProviderRole.LICENSOR]})
    providers.append({"name": arguments.producer, "roles": [ProviderRole.PRODUCER]})

    collection = ImageryCollection(
        title=arguments.title, description=arguments.description, collection_id=arguments.collection_id, providers=providers
    )

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    s3_client = client("s3")

    files_to_read = list_json_in_uri(uri, s3_client)

    start_time = time_in_ms()
    for key, result in get_object_parallel_multithreading(
        bucket_name_from_path(uri), files_to_read, s3_client, arguments.concurrency
    ):
        item_stac = json.loads(result["Body"].read().decode("utf-8"))

        if not arguments.collection_id == item_stac["collection"]:
            get_log().trace(
                "skipping: item.collection != collection.id",
                path=key,
                action="collection_from_items",
                reason="skip",
            )
            continue

        collection.add_item(item_stac)
        get_log().info("item added to collection", item=item_stac["id"], path=key)

    get_log().info(
        "Matching items added to collection",
        item_count=len(files_to_read),
        item_match_count=[dictionary["rel"] for dictionary in collection.stac["links"]].count("item"),
        duration=time_in_ms() - start_time,
    )

    destination = os.path.join(uri, "collection.json")
    collection.write_to(destination)
    get_log().info("collection written", destination=destination)


if __name__ == "__main__":
    main()
