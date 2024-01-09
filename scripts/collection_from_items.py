import argparse
import json
import os
from typing import List

from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import coalesce_multi_single, valid_date
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_json_in_uri
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import DATA_CATEGORIES, HUMAN_READABLE_REGIONS, CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole


# pylint: disable-msg=too-many-locals
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Collection ID", required=True)
    parser.add_argument(
        "--category",
        dest="category",
        help="Dataset category description",
        required=True,
        choices=DATA_CATEGORIES.keys(),
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
        "--location", dest="location", help="Optional Location of dataset, e.g. Hutt City", type=str, required=False
    )
    parser.add_argument(
        "--geographic-description",
        dest="geographic_description",
        help="Optional Location Name, e.g. South Island",
        type=str,
        required=False,
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
        help="Historic Survey Number if Applicable. E.g. SCN8844",
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

    collection_metadata: CollectionMetadata = {
        "category": arguments.category,
        "region": arguments.region,
        "gsd": arguments.gsd,
        "start_datetime": arguments.start_date,
        "end_datetime": arguments.end_date,
        "lifecycle": arguments.lifecycle,
        "location": arguments.location,
        "event_name": arguments.event,
        "historic_survey_number": arguments.historic_survey_number,
        "geographic_description": arguments.geographic_description,
    }

    collection = ImageryCollection(
        metadata=collection_metadata,
        collection_id=arguments.collection_id,
        providers=providers,
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

        if not arguments.collection_id == item_stac.get("collection"):
            get_log().trace(
                "skipping: item.collection != collection.id",
                file=key,
                action="collection_from_items",
                reason="skip",
            )
            continue

        collection.add_item(item_stac)
        get_log().info("item added to collection", item=item_stac["id"], file=key)

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
