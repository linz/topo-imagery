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
from scripts.stac.imagery.generate_metadata import generate_description, generate_title
from scripts.stac.imagery.provider import Provider, ProviderRole


# pylint: disable-msg=too-many-locals
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True, help="Standardised file format. Example: webp")
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Collection ID", required=True)
    parser.add_argument("--subtype", dest="subtype", help="Dataset subtype description", required=True)
    parser.add_argument("--region", dest="region", help="Region of Dataset", required=True)
    parser.add_argument("--gsd", dest="gsd", help="GSD of imagery Dataset", required=True)
    parser.add_argument("--location", dest="location", help="Optional Location of dataset, e.g.- Hutt City", required=False)
    parser.add_argument(
        "--start-datetime", dest="start_datetime", help="Start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end-datetime", dest="end_datetime", help="End datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--event", dest="dest", help="Event name if applicable", required=False)
    parser.add_argument(
        "--historic-survey-number", dest="historic_survey_number", help="Historic Survey Number if Applicable", required=False
    )
    parser.add_argument("--lifecycle", dest="lifecycle", help="Designating dataset status", required=True)
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

    title = generate_title(
        arguments.subtype,
        arguments.region,
        arguments.gsd,
        arguments.start_datetime,
        arguments.end_datetime,
        arguments.lifecycle,
        arguments.location,
        arguments.event,
        arguments.historic_survey_number,
    )
    description = generate_description(
        arguments.subtype,
        arguments.region,
        arguments.start_datetime,
        arguments.end_datetime,
        arguments.location,
        arguments.event,
        arguments.historic_survey_number,
    )

    collection = ImageryCollection(
        title=title, description=description, collection_id=arguments.collection_id, providers=providers
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
