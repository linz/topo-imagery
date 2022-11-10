import json
from typing import Any, Dict, List, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import parse_source
from scripts.files.file_check import FileCheck
from scripts.files.files_helper import is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdalinfo import format_wkt, gdal_info
from scripts.logging.time_helper import time_in_ms


def non_visual_qa(files: List[str]) -> None:
    start_time = time_in_ms()

    get_log().info("non_visual_qa_start")

    srs = get_srs()

    for file in files:
        if not is_tiff(file):
            get_log().trace("non_visual_qa_file_not_tiff_skipped", file=file)
            continue
        get_log().info(f"Non Visual QA {file}", file=file)

        qa_file(file, srs)

    get_log().info("non_visual_qa_end", duration=time_in_ms() - start_time)


def get_srs() -> bytes:
    gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", "EPSG:2193"]
    gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
    if gdalsrsinfo_result.stderr:
        raise Exception(
            f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr!r}"
        )
    return gdalsrsinfo_result.stdout


def qa_file(file: str, srs: bytes, gdalinfo_result: Optional[Dict[Any, Any]] = None) -> None:
    file_check = FileCheck(file, srs)
    if not gdalinfo_result:
        gdalinfo_result = gdal_info(path=file, file_check=file_check)
    file_check.validate(gdalinfo_result)

    # Format gdalinfo for logging
    gdalinfo_result["coordinateSystem"]["wkt"] = format_wkt(gdalinfo_result["coordinateSystem"]["wkt"])
    gdalinfo_result["stac"]["proj:wkt2"] = format_wkt(gdalinfo_result["stac"]["proj:wkt2"])
    gdalinfo_formatted = json.dumps(gdalinfo_result)
    # Non Visual QA Report
    if not file_check.is_valid():
        get_log().info("non_visual_qa_errors", file=file_check.path, errors=file_check.errors, gdalinfo=gdalinfo_formatted)
    else:
        get_log().info("non_visual_qa_passed", file=file_check.path)


def main() -> None:
    source = parse_source()
    non_visual_qa(source)


if __name__ == "__main__":
    main()
