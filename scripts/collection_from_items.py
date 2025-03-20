import argparse
import json
import os
from argparse import Namespace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

import shapely.geometry
import shapely.ops
from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import coalesce_multi_single, str_to_bool, str_to_gsd
from scripts.datetimes import RFC_3339_DATETIME_FORMAT, parse_rfc_3339_datetime
from scripts.files.files_helper import SUFFIX_JSON
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_files_in_uri
from scripts.gdal.gdal_footprint import SUFFIX_FOOTPRINT
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import CollectionIdentifiers
from scripts.stac.imagery.create_stac import CreateCollectionOptions, create_collection
from scripts.stac.imagery.metadata_constants import DATA_CATEGORIES, HUMAN_READABLE_REGIONS, CollectionMetadata

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = GetObjectOutputTypeDef = dict


class NoItemsError(Exception):
    pass


def parse_args(args: List[str] | None) -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", help="s3 path to items and collection.json write location", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Collection ID", required=True)
    parser.add_argument(
        "--odr-url",
        dest="odr_url",
        help="The path of the published dataset. Example: 's3://nz-imagery/wellington/porirua_2024_0.1m/rgb/2193/'",
        required=False,
    )
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
    parser.add_argument("--gsd", dest="gsd", help="GSD of imagery Dataset, for example 0.3", type=str_to_gsd, required=True)
    parser.add_argument(
        "--geographic-description",
        dest="geographic_description",
        help="Optional Geographic Description of dataset, e.g. Hutt City",
        type=str,
        required=False,
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
        "--linz-slug",
        dest="linz_slug",
        help="linz:slug attribute for this dataset. E.g. bay-of-plenty_2018-2019_0.1m",
        type=str,
        required=True,
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
    parser.add_argument(
        "--capture-dates",
        dest="capture_dates",
        help="Add a capture-dates.geojson.gz file to the collection assets",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--add-title-suffix",
        dest="add_title_suffix",
        help="Add a title suffix to the collection title based on the lifecycle. For example, '[TITLE] - Preview'",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--current-datetime",
        dest="current_datetime",
        help=(
            "The datetime to be used as current datetime in the metadata. "
            "Format: RFC 3339 UTC datetime, `YYYY-MM-DDThh:mm:ssZ`."
        ),
        required=False,
        default=datetime.now(timezone.utc).strftime(RFC_3339_DATETIME_FORMAT),
    )

    return parser.parse_args(args)


# pylint: disable=too-many-locals
def main(args: List[str] | None = None) -> None:
    start_time = time_in_ms()
    arguments = parse_args(args)
    uri = arguments.uri
    collection_id = arguments.collection_id

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    s3_client: S3Client = client("s3")

    files_to_read = list_files_in_uri(uri, [SUFFIX_JSON, SUFFIX_FOOTPRINT], s3_client)

    items_to_add = []
    start_datetime = ""
    end_datetime = ""
    polygons = []
    for key, result in get_object_parallel_multithreading(
        bucket_name_from_path(uri), files_to_read, s3_client, arguments.concurrency
    ):
        content = json.load(result["Body"])
        # The following if/else looks like it could be avoid by refactoring `list_files_in_uri()`
        # to return a result list per suffix, but we would have to call `get_object_parallel_multithreading()`
        # for each of them to avoid this if/else.
        if key.endswith(SUFFIX_JSON):
            if content["type"] != "Feature":
                get_log().warn(
                    "skipping: not a STAC item",
                    file=key,
                    action="collection_from_items",
                    reason="skip",
                )
                continue
            item_collection_id = content.get("collection")
            if collection_id != item_collection_id:
                get_log().warn(
                    f"skipping: {item_collection_id} and {collection_id} do not match",
                    file=key,
                    action="collection_from_items",
                    reason="skip",
                )
                continue
            items_to_add.append(content)
            if not start_datetime or content["properties"]["start_datetime"] < start_datetime:
                start_datetime = content["properties"]["start_datetime"]
            if not end_datetime or content["properties"]["end_datetime"] > end_datetime:
                end_datetime = content["properties"]["end_datetime"]
            get_log().info("Item will be added to Collection", item=content["id"], file=key)
        elif key.endswith(SUFFIX_FOOTPRINT):
            get_log().debug(f"adding geometry from {key}")
            polygons.append(shapely.geometry.shape(content["features"][0]["geometry"]))

    if len(items_to_add) == 0:
        get_log().error(
            f"Collection {collection_id} has no items. Collection will not be created.",
        )
        raise NoItemsError(f"Collection {collection_id} has no items")

    collection_metadata: CollectionMetadata = {
        "category": arguments.category,
        "region": arguments.region,
        "gsd": arguments.gsd,
        "start_datetime": parse_rfc_3339_datetime(start_datetime),
        "end_datetime": parse_rfc_3339_datetime(end_datetime),
        "lifecycle": arguments.lifecycle,
        "geographic_description": arguments.geographic_description,
        "event_name": arguments.event,
        "historic_survey_number": arguments.historic_survey_number,
    }

    collection = create_collection(
        collection_identifiers=CollectionIdentifiers(arguments.linz_slug, collection_id),
        collection_metadata=collection_metadata,
        current_datetime=arguments.current_datetime,
        producers=coalesce_multi_single(arguments.producer_list, arguments.producer),
        licensors=coalesce_multi_single(arguments.licensor_list, arguments.licensor),
        stac_items=items_to_add,
        item_polygons=polygons,
        options=CreateCollectionOptions(
            add_capture_dates=arguments.capture_dates, add_title_suffix=arguments.add_title_suffix
        ),
        uri=uri,
        odr_url=arguments.odr_url,
    )

    destination = os.path.join(uri, "collection.json")
    collection.write_to(destination)

    get_log().info(
        "Collection created",
        item_count=len(files_to_read),
        item_match_count=items_to_add,
        duration=time_in_ms() - start_time,
        destination=destination,
    )


if __name__ == "__main__":
    main()
