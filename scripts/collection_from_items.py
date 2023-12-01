import argparse
import json
import os
from typing import List

import geojson
import shapely.geometry
import shapely.ops
from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import coalesce_multi_single
from scripts.files.files_helper import ContentType
from scripts.files.fs import write
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_files_in_uri
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import CAPTURE_AREA_FILE_NAME, ImageryCollection
from scripts.stac.imagery.provider import Provider, ProviderRole


def main() -> None:
    # pylint: disable-msg=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Collection ID", required=True)
    parser.add_argument("--title", dest="title", help="Collection title", required=True)
    parser.add_argument("--description", dest="description", help="Collection description", required=True)
    parser.add_argument(
        "--producer",
        dest="producer",
        help="Imagery producer. Ignored if --producer-list passed with a semicolon delimited list.",
    )
    parser.add_argument("--producer-list", dest="producer_list", help="Semicolon delimited list of imagery producers")
    parser.add_argument(
        "--licensor",
        dest="licensor",
        help="Imagery licensor. Ignored if --licensor-list passed with a semicolon delimited list.",
    )
    parser.add_argument("--licensor-list", dest="licensor_list", help="Semicolon delimited list of imagery licensors")
    parser.add_argument(
        "--concurrency", dest="concurrency", help="The number of files to limit concurrent reads", required=True, type=int
    )

    arguments = parser.parse_args()
    uri = arguments.uri

    providers: List[Provider] = []
    for producer_name in coalesce_multi_single(arguments.producer_list, arguments.producer):
        providers.append({"name": producer_name, "roles": [ProviderRole.PRODUCER]})
    for licensor_name in coalesce_multi_single(arguments.licensor_list, arguments.licensor):
        providers.append({"name": licensor_name, "roles": [ProviderRole.LICENSOR]})

    collection = ImageryCollection(
        title=arguments.title, description=arguments.description, collection_id=arguments.collection_id, providers=providers
    )

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    s3_client = client("s3")

    files_to_read = list_files_in_uri(uri, (".json", "_footprint.geojson"), s3_client)

    start_time = time_in_ms()
    polygons = []
    for key, result in get_object_parallel_multithreading(
        bucket_name_from_path(uri), files_to_read, s3_client, arguments.concurrency
    ):
        content = json.loads(result["Body"].read().decode("utf-8"))

        if key.endswith(".json"):
            if not arguments.collection_id == content.get("collection"):
                get_log().trace(
                    "skipping: item.collection != collection.id",
                    file=key,
                    action="collection_from_items",
                    reason="skip",
                )
                continue
            collection.add_item(content)
            get_log().info("item added to collection", item=content["id"], file=key)
        elif key.endswith("_footprint.geojson"):
            get_log().debug(f"adding geometry from {key}")
            geom = shapely.geometry.shape(content["features"][0]["geometry"])
            polygons.append(geom)

    capture_area = geojson.Feature(geometry=shapely.ops.unary_union(polygons), properties={})
    write(
        os.path.join(uri, CAPTURE_AREA_FILE_NAME),
        json.dumps(capture_area).encode("utf-8"),
        content_type=ContentType.GEOJSON.value,
    )

    get_log().info(
        "Matching items added to collection and capture-area created",
        item_count=len(files_to_read),
        item_match_count=[dictionary["rel"] for dictionary in collection.stac["links"]].count("item"),
        duration=time_in_ms() - start_time,
    )

    destination = os.path.join(uri, "collection.json")
    collection.write_to(destination)
    get_log().info("collection written", destination=destination)


if __name__ == "__main__":
    main()
