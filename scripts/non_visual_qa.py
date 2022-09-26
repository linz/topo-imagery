from typing import List

from linz_logger import get_log

from scripts.cli.cli_helper import parse_source
from scripts.files.file_check import FileCheck
from scripts.files.files_helper import is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdalinfo import gdal_info
from scripts.logging.time_helper import time_in_ms


def non_visual_qa(files: List[str]) -> None:
    start_time = time_in_ms()

    get_log().info("non_visual_qa_start")

    # Get srs
    gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", "EPSG:2193"]
    gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
    if gdalsrsinfo_result.stderr:
        raise Exception(
            f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr!r}"
        )
    srs = gdalsrsinfo_result.stdout

    for file in files:
        if not is_tiff(file):
            get_log().trace("non_visual_qa_file_not_tiff_skipped", file=file)
            continue
        get_log().info(f"Non Visual QA {file}", file=file)
        file_check = FileCheck(file, srs)
        gdalinfo_result = gdal_info(path=file, file_check=file_check)
        file_check.validate(gdalinfo_result)

        if not file_check.is_valid():
            get_log().info("non_visual_qa_errors", file=file_check.path, errors=file_check.errors)
        else:
            get_log().info("non_visual_qa_passed", file=file_check.path)

    get_log().info("non_visual_qa_end", duration=time_in_ms() - start_time)


def main() -> None:
    source = parse_source()
    non_visual_qa(source)


if __name__ == "__main__":
    main()
