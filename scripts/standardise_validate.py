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
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--scale", dest="scale", required=True)
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
    collection_id = arguments.collection_id
    concurrency: int = 1
    if is_argo():
        concurrency = 4

    # Standardize the tiffs
    tiff_files = run_standardising(source, arguments.preset, concurrency)
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
            get_log().info(
                "non_visual_qa_errors",
                originalPath=file.get_path_original(),
                errors=file.get_errors(),
            )
        else:
            get_log().info("non_visual_qa_passed", path=file.get_path_original())

        # Create STAC
        item = create_item(file.get_path_standardised(), start_datetime, end_datetime, collection_id, file.get_gdalinfo())
        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac_saved", path=tmp_file_path)


if __name__ == "__main__":
    main()
