import argparse

from linz_logger import get_log

from scripts.cli.cli_helper import format_source, is_argo
from scripts.files.files_helper import is_tiff
from scripts.gdal.gdalinfo import gdal_info
from scripts.non_visual_qa import get_srs, qa_file
from scripts.standardising import start_standardising


def main() -> None:

    concurrency: int = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)

    arguments = parser.parse_args()

    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    standardised_files = start_standardising(source, arguments.preset, concurrency)
    if not standardised_files:
        get_log().info("Process skipped because no file has been standardised", action="standardise_validate", reason="skip")
        return
    srs = get_srs()

    for file in standardised_files:
        if not is_tiff(file):
            get_log().trace("file_not_tiff_skipped", file=file)
            continue
        gdalinfo_result = gdal_info(file)
        qa_file(file, srs, gdalinfo_result)


if __name__ == "__main__":
    main()
