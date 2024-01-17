import argparse
import json
import os
from typing import List

import shapely.geometry
import shapely.ops
from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import coalesce_multi_single, valid_date
from scripts.files.files_helper import SUFFIX_FOOTPRINT, SUFFIX_JSON
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_files_in_uri
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import (
    HUMAN_READABLE_REGIONS,
    CollectionTitleMetadata,
    ElevationCategories,
    ImageryCategories,
)
from scripts.stac.imagery.provider import Provider, ProviderRole


# pylint: disable=too-many-locals
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Collection ID", required=True)
    parser.add_argument(
        "--category",
        dest="category",
        help="Dataset category description",
        required=True,
        choices=[type.value for type in ImageryCategories] + [type.value for type in ElevationCategories],
    )
    parser.add_argument(
        "--region",
        dest="region",
        help="Region of Dataset",
        required=True,
        choices=HUMAN_READABLE_REGIONS.keys(),
    )
    parser.add_argument("--gsd", dest="gsd", help="GSD of imagery Dataset", type=str, required=True)
    parser.add_argument(
        "--location", dest="location", help="Optional Location of dataset, e.g.- Hutt City", type=str, required=False
    )
    parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Start date in format YYYY-MM-DD (Inclusive)",
        type=valid_date,
        required=True,
    )
    parser.add_argument(
        "--end-date", dest="end_date", help="End date in format YYYY-MM-DD (Inclusive)", type=valid_date, required=True
    )
    parser.add_argument("--event", dest="event", help="Event name if applicable", type=str, required=False)
    parser.add_argument(
        "--historic-survey-number",
        dest="historic_survey_number",
        help="Historic Survey Number if Applicable. E.g.- SCN8844",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--lifecycle",
        dest="lifecycle",
        help="Designating dataset status",
        required=True,
        choices=["under development", "preview", "ongoing", "completed", "deprecated"],
    )
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

    title_metadata: CollectionTitleMetadata = {
        "category": arguments.category,
        "region": arguments.region,
        "gsd": arguments.gsd,
        "start_datetime": arguments.start_date,
        "end_datetime": arguments.end_date,
        "lifecycle": arguments.lifecycle,
        "location": arguments.location,
        "event": arguments.event,
        "historic_survey_number": arguments.historic_survey_number,
    }

    collection = ImageryCollection(title_metadata=title_metadata, collection_id=arguments.collection_id, providers=providers)

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    s3_client = client("s3")

    files_to_read = list_files_in_uri(uri, [SUFFIX_JSON, SUFFIX_FOOTPRINT], s3_client)

    start_time = time_in_ms()
    polygons = []
    for key, result in get_object_parallel_multithreading(
        bucket_name_from_path(uri), files_to_read, s3_client, arguments.concurrency
    ):
        content = json.load(result["Body"])
        # The following if/else looks like it could be avoid by refactoring `list_files_in_uri()`
        # to return a result list per suffix, but we would have to call `get_object_parallel_multithreading()`
        # for each of them to avoid this if/else.
        if key.endswith(SUFFIX_JSON):
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
        elif key.endswith(SUFFIX_FOOTPRINT):
            get_log().debug(f"adding geometry from {key}")
            polygons.append(shapely.geometry.shape(content["features"][0]["geometry"]))

    if polygons:
        collection.add_capture_area(polygons, uri)

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
