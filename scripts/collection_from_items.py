import argparse
import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from boto3 import client
from linz_logger import get_log

from scripts.cli.cli_helper import coalesce_multi_single, get_geometry_from_geojson, str_to_bool, str_to_gsd
from scripts.cli.common_args import CommonArgumentParser
from scripts.datetimes import RFC_3339_DATETIME_FORMAT
from scripts.files.files_helper import SUFFIX_JSON
from scripts.files.fs_s3 import bucket_name_from_path, get_object_parallel_multithreading, list_files_in_uri, read
from scripts.gdal.gdal_footprint import SUFFIX_FOOTPRINT
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.collection import COLLECTION_FILE_NAME
from scripts.stac.imagery.collection_context import CollectionContext
from scripts.stac.imagery.constants import DATA_CATEGORIES, DATA_DOMAINS, HUMAN_READABLE_REGIONS, LAND
from scripts.stac.imagery.create_stac import create_collection

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = GetObjectOutputTypeDef = dict


class NoItemsError(Exception):
    pass


def get_args_parser() -> CommonArgumentParser:
    parser = CommonArgumentParser(
        description=(
            "Create a STAC Collection from existing STAC Items in a given S3 URI. "
            "Generate a capture-area file if footprint files are present."
        )
    )
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
        help="Dataset category",
        required=True,
        choices=DATA_CATEGORIES.keys(),
    )
    parser.add_argument(
        "--domain",
        dest="domain",
        help="Dataset domain",
        default=LAND,
        choices=DATA_DOMAINS.keys(),
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
        help="Add a capture-dates.geojson.gz file to the Collection assets",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--add-title-suffix",
        dest="add_title_suffix",
        help="Add a title suffix to the Collection title based on the lifecycle. For example, '[TITLE] - Preview'",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--keep-description",
        dest="keep_description",
        help="Keep the description of the existing Collection as is.",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--keep-title",
        dest="keep_title",
        help="Keep the title of the existing Collection as is.",
        type=str_to_bool,
        required=False,
    )
    parser.add_argument(
        "--delete-all-existing-items",
        dest="delete_all_existing_items",
        help="Delete all existing Items in the collection before adding new Items. "
        "To use in the case of re-creating an existing dataset.",
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
    parser.add_argument(
        "--supplied-capture-area",
        dest="supplied_capture_area",
        help="Optional externally supplied EPSG:4326 capture area",
        required=False,
        nargs="?",
    )
    parser.add_argument(
        "--simplified-capture-area",
        dest="simplified_capture_area",
        help="Whether the individual item footprints have been simplified.",
        required=False,
        default=False,
        type=str_to_bool,
    )

    return parser


# pylint: disable=too-many-locals
def main(args: List[str] | None = None) -> None:
    start_time = time_in_ms()
    parser = get_args_parser()
    arguments = parser.parse_args(args)
    uri = arguments.uri
    collection_id = arguments.collection_id
    supplied_capture_area = arguments.supplied_capture_area
    simplified_capture_area = arguments.simplified_capture_area

    if not uri.startswith("s3://"):
        msg = f"uri is not a s3 path: {uri}"
        raise argparse.ArgumentTypeError(msg)

    if supplied_capture_area and simplified_capture_area:
        parser.error("--simplified-capture-area cannot be True when --supplied-capture-area is set.")

    s3_client: S3Client = client("s3")

    files_to_read = list_files_in_uri(uri, [SUFFIX_JSON, SUFFIX_FOOTPRINT], s3_client)

    items_to_add = []
    polygons = []

    if supplied_capture_area:
        content = json.loads(read(supplied_capture_area))
        polygons.append(get_geometry_from_geojson(content, supplied_capture_area))

    for key, result in get_object_parallel_multithreading(
        bucket_name_from_path(uri), files_to_read, s3_client, arguments.concurrency
    ):
        content = json.load(result["Body"])
        # The following if/else looks like it could be avoided by refactoring `list_files_in_uri()`
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
            get_log().info("Item will be added to Collection", item=content["id"], file=key)
        elif key.endswith(SUFFIX_FOOTPRINT) and not arguments.supplied_capture_area:
            polygons.append(get_geometry_from_geojson(content, key))

    if len(items_to_add) == 0:
        get_log().error(
            f"Collection {collection_id} has no items. Collection will not be created.",
        )
        raise NoItemsError(f"Collection {collection_id} has no items")

    collection_context = CollectionContext(
        category=arguments.category,
        domain=arguments.domain,
        region=arguments.region,
        gsd=arguments.gsd,
        lifecycle=arguments.lifecycle,
        linz_slug=arguments.linz_slug,
        collection_id=collection_id,
        geographic_description=arguments.geographic_description,
        event_name=arguments.event,
        historic_survey_number=arguments.historic_survey_number,
        producers=coalesce_multi_single(arguments.producer_list, arguments.producer),
        licensors=coalesce_multi_single(arguments.licensor_list, arguments.licensor),
        add_title_suffix=arguments.add_title_suffix,
        add_capture_dates=arguments.capture_dates,
        delete_existing_items=arguments.delete_all_existing_items,
        keep_description=arguments.keep_description,
        keep_title=arguments.keep_title,
    )

    collection = create_collection(
        collection_context=collection_context,
        current_datetime=arguments.current_datetime,
        stac_items=items_to_add,
        item_polygons=polygons,
        uri=uri,
        odr_url=arguments.odr_url,
        supplied_capture_area=supplied_capture_area,
        simplified_capture_area=simplified_capture_area,
    )

    destination = os.path.join(uri, COLLECTION_FILE_NAME)
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
