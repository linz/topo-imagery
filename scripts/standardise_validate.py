import argparse

from linz_logger import get_log

from scripts.cli.cli_helper import format_source, is_argo, valid_date
from scripts.create_stac_items import create_item
from scripts.files.files_helper import is_tiff
from scripts.gdal.gdalinfo import gdal_info
from scripts.non_visual_qa import get_srs, qa_file
from scripts.stac.imagery.collection import ImageryCollection
from scripts.standardising import start_standardising


def main() -> None:

    concurrency: int = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=False
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=False
    )
    parser.add_argument("--collection", dest="collection", help="path to collection.json", required=False)

    arguments = parser.parse_args()

    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    standardised_files = start_standardising(source, arguments.preset, concurrency)
    if not standardised_files:
        get_log().info("Process skipped because no file has been standardised", action="standardise_validate", reason="skip")
        return
    srs = get_srs()

    if not arguments.collection or not arguments.start_datetime or not arguments.end_datetime:
        get_log().trace("required_args_not_parsed_create_stac_skipped", action="standardise_validate", reason="skip")
        collection = None
    else:
        collection = ImageryCollection(path=arguments.collection)

    for file in standardised_files:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue
        gdalinfo_result = gdal_info(file)
        validity = qa_file(file, srs, gdalinfo_result)
        if not validity:
            get_log().trace("file_not_valid_create_stac_skipped", file=file)
            continue
        if collection:
            create_item(file, arguments.start_datetime, arguments.end_datetime, collection, gdalinfo_result)


if __name__ == "__main__":
    main()
