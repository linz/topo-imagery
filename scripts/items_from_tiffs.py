import argparse
import sys
from datetime import datetime, timezone

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, item_stac_wrapper, load_input_files, valid_date
from scripts.datetimes import RFC_3339_DATETIME_FORMAT


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

    item_stac_wrapper(tile_files, arguments)


if __name__ == "__main__":
    main()
