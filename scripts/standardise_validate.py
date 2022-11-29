import argparse
import json
import os

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac import create_item
from scripts.files.file_check import FileCheck
from scripts.files.files_helper import is_tiff
from scripts.files.fs import write
from scripts.gdal.gdal_helper import get_srs
from scripts.standardising import start_standardising
from scripts.gdal.gdalinfo import format_wkt


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
    parser.add_argument("--origin-correction", dest="origin_correction", required=False)
    arguments = parser.parse_args()

    source = format_source(arguments.source)
    scale = int(arguments.scale)
    start_datetime = format_date(arguments.start_datetime)
    end_datetime = format_date(arguments.end_datetime)
    concurrency: int = 1
    if is_argo():
        concurrency = 4
    origin_correction = None
    try:
        origin_correction = float(arguments.origin_correction)
    except TypeError:
        get_log().info("no_origin_correction_specified")

    standardised_files = start_standardising(source, arguments.preset, concurrency)
    if not standardised_files:
        get_log().info("Process skipped because no file has been standardised", action="standardise_validate", reason="skip")
        return
    # SRS needed for FileCheck (non visual QA)
    srs = get_srs()
    for file in standardised_files:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue

        # Validate the file
        file_check = FileCheck(file, scale, srs, origin_correction)
        if not file_check.validate():
            # Format gdalinfo for logging
            formatted_gdalinfo = file_check.get_gdalinfo()
            if formatted_gdalinfo:
                formatted_gdalinfo["coordinateSystem"]["wkt"] = format_wkt(formatted_gdalinfo["coordinateSystem"]["wkt"])
                formatted_gdalinfo["stac"]["proj:wkt2"] = format_wkt(formatted_gdalinfo["stac"]["proj:wkt2"])
            get_log().info("non_visual_qa_errors", file=file_check.path, errors=file_check.errors, gdalinfo=formatted_gdalinfo)
        else:
            get_log().info("non_visual_qa_passed", file=file_check.path)
        # Get the new path if the file has been renamed
        file = file_check.path
        # Create STAC
        gdalinfo = file_check.get_gdalinfo()
        item = create_item(file, start_datetime, end_datetime, arguments.collection_id, gdalinfo)
        tmp_file_path = os.path.join("/tmp/", f"{item.stac['id']}.json")
        write(tmp_file_path, json.dumps(item.stac).encode("utf-8"))
        get_log().info("stac item written to tmp", location=tmp_file_path)


if __name__ == "__main__":
    main()
