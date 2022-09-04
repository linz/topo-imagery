import argparse
import os
import sys
from functools import partial
from multiprocessing import Pool
from typing import List

from linz_logger import get_log

from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import format_source, is_argo
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_gdal_command
from scripts.logging.time_helper import time_in_ms


def start_standardising(files: List[str], preset: str, concurrency: int) -> List[str]:
    start_time = time_in_ms()
    tiff_files = []
    output_files = []

    get_log().info("standardising_start")

    for file in files:
        if is_tiff(file):
            tiff_files.append(file)
        else:
            get_log().info("standardising_file_not_tiff_skipped", file=file)

    with Pool(concurrency) as p:
        output_files = p.map(partial(standardising, preset=preset), tiff_files)
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time)

    return output_files


def standardising(file: str, preset: str) -> str:
    output_folder = "/tmp/"

    get_log().info(f"standardising {file}", source=file)

    _, src_file_path = parse_path(file)
    standardized_file_name = f"{get_file_name_from_path(src_file_path)}.tiff"
    tmp_file_path = os.path.join(output_folder, standardized_file_name)

    command = get_gdal_command(preset)
    run_gdal(command, input_file=file, output_file=tmp_file_path)

    return tmp_file_path


def main() -> None:
    concurrency: int = 1
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser.parse_args()
    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    start_standardising(source, arguments.preset, concurrency)


if __name__ == "__main__":  # pylint: disable=duplicate-code
    try:
        main()
    except Exception as ex:  # pylint:disable=broad-except
        get_log().error("An error occured while executing standardising.py", error=str(ex))
        sys.exit(1)
