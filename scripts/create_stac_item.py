import argparse
import os
from datetime import datetime, timezone

from linz_logger import get_log

from scripts.cli.cli_helper import valid_date
from scripts.datetimes import (
    RFC_3339_DATETIME_FORMAT,
    format_rfc_3339_nz_midnight_datetime_string,
)
from scripts.files.files_helper import SUFFIX_JSON, ContentType
from scripts.files.fs import write
from scripts.gdal.gdal_helper import gdal_info
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.create_stac import create_item
from scripts.standardise_validate import str_to_bool


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset",
        dest="asset",
        help="Specify the path to the asset to create the STAC Item for.",
    )
    parser.add_argument(
        "--derived-from",
        dest="derived_from",
        help="Specify the STAC Items the asset is derived from. Separated by comma.",
    )
    parser.add_argument(
        "--from-file",
        dest="from_file",
        help="Specify the path to a json file containing a list of path to the asset and the Items it is derived from (if any). Format: [{'path': 'path/to/asset.tiff', 'derivedFrom': ['path/to/derived1.json', 'path/to/derived2.json']}]",
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
    parser.add_argument(
        "--create-footprints",
        dest="create_footprints",
        help="Create footprints for each tile ('true' / 'false')",
        type=str_to_bool,
        required=True,
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

    parser.add_argument(
        "--gdal-version",
        dest="gdal_version",
        help=("Specify GDAL version that was used to create the asset. "),
        required=False,
        default=os.environ["GDAL_VERSION"],
    )
    return parser


def main() -> None:
    parser = get_args_parser()
    arguments = parser.parse_args()

    asset_inputs = []
    if arguments.asset and arguments.derived_from:
        asset_inputs.append({"path": arguments.asset, "derivedFrom": arguments.derived_from.split(",")})
    elif arguments.from_file:
        parser.error("--from_file not implemented yet.")
    else:
        parser.error(
            "Missing required argument(s) for STAC creation. Provide either --asset and --derived-from, or --from-file.",
        )

    # When standardising output includeDerived, start_datetime and end_datetime are optional
    if arguments.start_datetime is None or arguments.end_datetime is None:
        for asset in asset_inputs:
            if not asset.get("derivedFrom"):
                parser.error("--start_datetime and --end_datetime are required if creating STAC for non-derived files.")
        start_datetime = ""
        end_datetime = ""
    else:
        start_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.start_datetime)
        end_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.end_datetime)

    # concurrency: int = 1
    # if is_argo():
    #     concurrency = 4

    for asset in asset_inputs:
        path = asset["path"]
        derived_from = asset.get("derivedFrom", [])
        # Create STAC and save in target
        item = create_item(
            path,
            start_datetime,
            end_datetime,
            arguments.collection_id,
            arguments.gdal_version,
            arguments.current_datetime,
            gdal_info(path),
            derived_from,
            arguments.odr_url,
        )
        stac_item_path = path.rsplit(".", 1)[0] + SUFFIX_JSON
        write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)
        get_log().info("stac_saved", path=stac_item_path)


if __name__ == "__main__":
    main()
