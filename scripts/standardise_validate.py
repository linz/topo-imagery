import argparse
import os
import sys

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, is_argo, load_input_files, valid_date
from scripts.datetimes import format_rfc_3339_nz_midnight_datetime_string
from scripts.files.files_helper import SUFFIX_JSON, ContentType
from scripts.files.fs import exists, write
from scripts.gdal.gdal_helper import get_srs, get_vfs_path
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.create_stac import create_item
from scripts.standardising import run_standardising


def str_to_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean (must be exactly 'true' or 'false'): {value}")


def main() -> None:
    # pylint: disable-msg=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True, help="Standardised file format. Example: webp")
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--source-epsg", dest="source_epsg", required=True, help="The EPSG code of the source imagery")
    parser.add_argument(
        "--target-epsg",
        dest="target_epsg",
        required=True,
        help="The target EPSG code. If different to source the imagery will be reprojected",
    )
    parser.add_argument("--gsd", dest="gsd", help="GSD of imagery Dataset", type=str, required=True)
    parser.add_argument(
        "--create-footprints",
        dest="create_footprints",
        help="Create footprints for each tile ('true' / 'false')",
        type=str_to_bool,
        required=True,
    )
    parser.add_argument("--cutline", dest="cutline", help="Optional cutline to cut imagery to", required=False, nargs="?")
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime", dest="start_datetime", help="Start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end-datetime", dest="end_datetime", help="End datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--target", dest="target", help="Target output", required=True)
    arguments = parser.parse_args()

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)
    start_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.start_datetime)
    end_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.end_datetime)
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    tiff_files = run_standardising(
        tile_files,
        arguments.preset,
        arguments.cutline,
        concurrency,
        arguments.source_epsg,
        arguments.target_epsg,
        arguments.gsd,
        arguments.create_footprints,
        arguments.target,
    )

    if len(tiff_files) == 0:
        get_log().info("no_tiff_to_process", action="standardise_validate", reason="skipped")
        return

    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()

    for file in tiff_files:
        stac_item_path = file.get_path_standardised().rsplit(".", 1)[0] + SUFFIX_JSON
        if not exists(stac_item_path):
            file.set_srs(srs)

            # Validate the file
            if not file.validate():
                # If the file is not valid (Non Visual QA errors)
                # Logs the `vsis3` path to use `gdal` on the file directly from `s3`
                # This is to help data analysts to verify the file.
                original_path: list[str] = file.get_paths_original()
                standardised_path = file.get_path_standardised()
                env_argo_template = os.environ.get("ARGO_TEMPLATE")
                if env_argo_template:
                    standardised_path = get_vfs_path(file.get_path_standardised())
                    original_s3_path: list[str] = []
                    for path in original_path:
                        original_s3_path.append(get_vfs_path(path))
                    original_path = original_s3_path
                get_log().info(
                    "non_visual_qa_errors",
                    originalPath=",".join(original_path),
                    standardisedPath=standardised_path,
                    errors=file.get_errors(),
                )
            else:
                get_log().info("non_visual_qa_passed", path=file.get_path_standardised())

            # Create STAC and save in target
            item = create_item(
                file.get_path_standardised(), start_datetime, end_datetime, arguments.collection_id, file.get_gdalinfo()
            )
            write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)
            get_log().info("stac_saved", path=stac_item_path)


if __name__ == "__main__":
    main()
