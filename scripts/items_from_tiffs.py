import argparse
import os
import sys
from datetime import datetime, timezone

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, is_argo, load_input_files, valid_date
from scripts.datetimes import RFC_3339_DATETIME_FORMAT, format_rfc_3339_nz_midnight_datetime_string
from scripts.files.files_helper import ContentType, get_derived_from_paths, get_stac_item_path, get_standardised_file_path
from scripts.files.fs import exists, write
from scripts.gdal.gdal_helper import gdal_info
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.create_stac import create_item


def str_to_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean (must be exactly 'true' or 'false'): {value}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument(
        "--odr-url",
        dest="odr_url",
        help=(
            "The s3 URL of the published dataset in ODR if this is a re-supply. "
            "Example: 's3://nz-imagery/wellington/porirua_2024_0.1m/rgb/2193/'"
        ),
        required=False,
    )
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime",
        dest="start_datetime",
        help="Start datetime in format YYYY-MM-DD. Only optional if includeDerived.",
        type=valid_date,
    )
    parser.add_argument(
        "--end-datetime",
        dest="end_datetime",
        help="End datetime in format YYYY-MM-DD. Only optional if includeDerived.",
        type=valid_date,
    )
    parser.add_argument("--target", dest="target", help="Target output", required=True)
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
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    # When standardising output includeDerived, start_datetime and end_datetime are optional
    if arguments.start_datetime is None or arguments.end_datetime is None:
        for tile in tile_files:
            if not tile.includeDerived:
                raise Exception("--start_datetime and --end_datetime are required if standardising non-derived files.")
        start_datetime = ""
        end_datetime = ""
    else:
        start_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.start_datetime)
        end_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.end_datetime)

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    gdal_version = os.environ["GDAL_VERSION"]

    for tile in tile_files:
        derived_from_paths = []
        stac_item_path = get_stac_item_path(tile.output, arguments.target)
        standardized_file_path = get_standardised_file_path(tile.output, arguments.target)

        if tile.includeDerived:
            # Transform the TIFF paths to JSON path to point to STAC Items,
            # assuming the STAC Items are in the same directory as the TIFF files
            derived_from_paths = get_derived_from_paths(tile.inputs)

        if not exists(stac_item_path):
            # Create STAC and save in target
            item = create_item(
                standardized_file_path,
                start_datetime,
                end_datetime,
                arguments.collection_id,
                gdal_version,
                arguments.current_datetime,
                gdal_info(standardized_file_path),
                derived_from_paths,
                arguments.odr_url,
            )
            write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)
            get_log().info("stac_saved", path=stac_item_path)


if __name__ == "__main__":
    main()
