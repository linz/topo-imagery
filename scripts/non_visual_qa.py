from typing import Any, Dict, List, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import parse_source
from scripts.files.file_check import FileCheck
from scripts.files.files_helper import is_tiff
from scripts.gdal.gdal_helper import run_gdal
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
        qa_file(FileCheck(file, srs))

    get_log().info("non_visual_qa_end", duration=time_in_ms() - start_time)


def get_srs() -> bytes:
    gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", "EPSG:2193"]
    gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
    if gdalsrsinfo_result.stderr:
        raise Exception(
            f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr!r}"
        )
    return gdalsrsinfo_result.stdout


def qa_file(file: FileCheck) -> None:
    if not file.validate():
        get_log().info("non_visual_qa_errors", file=file.path, errors=file.errors)
    else:
        get_log().info("non_visual_qa_passed", file=file.path)


def main() -> None:
    source = parse_source()
    non_visual_qa(source)


if __name__ == "__main__":
    main()
