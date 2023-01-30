import argparse
import json
import os

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac import create_item
from scripts.files.fs import write
from scripts.gdal.gdal_helper import get_srs
from scripts.standardising import run_standardising


def main() -> None:
    # pylint: disable-msg=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--cutline", dest="cutline", help="Optional cutline to cut imagery to", required=False, nargs="?")
    parser.add_argument("--scale", dest="scale", help="Tile grid scale to align output tile to", required=True)
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end-datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    arguments = parser.parse_args()
    source = format_source(arguments.source)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    # Standardize the tiffs
    tiff_files = run_standardising(source, arguments.preset, arguments.cutline, concurrency)
    if len(tiff_files) == 0:
        get_log().info("no_tiff_file", action="standardise_validate", reason="skipped")
        return

    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()

    for file in tiff_files:
        file.set_srs(srs)
        file.set_scale(int(arguments.scale))

        # Validate the file
        if not file.validate():
            original_path = file.get_path_original()
            standardised_path = file.get_path_standardised()
            env_argo_template = os.environ.get("ARGO_TEMPLATE")
            if env_argo_template:
                argo_template = json.loads(env_argo_template)
                s3_information = argo_template["archiveLocation"]["s3"]
                standardised_path = os.path.join(
                    "/vsis3", s3_information["bucket"], s3_information["key"], file.get_path_standardised()
                )
                original_path = os.path.join(
                    "/vsis3", s3_information["bucket"], s3_information["key"], file.get_path_original()
                )
            get_log().info(
                "non_visual_qa_errors",
                originalPath=original_path,
                standardisedPath=standardised_path,
                errors=file.get_errors(),
            )
        else:
            get_log().info("non_visual_qa_passed", path=file.get_path_original())

        # Create STAC
        item = create_item(
            file.get_path_standardised(), start_datetime, end_datetime, arguments.collection_id, file.get_gdalinfo()
        )
        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac_saved", path=tmp_file_path)


if __name__ == "__main__":
    main()
