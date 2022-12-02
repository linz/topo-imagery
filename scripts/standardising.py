import argparse
import os
from functools import partial
from multiprocessing import Pool
from typing import List

from linz_logger import get_log

from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import format_source, is_argo
from scripts.files.file_tiff import FileTiff
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.gdal.gdal_helper import get_gdal_version, run_gdal
from scripts.gdal.gdal_preset import get_gdal_command
from scripts.logging.time_helper import time_in_ms


def run_standardising(files: List[str], preset: str, concurrency: int) -> List[FileTiff]:
    start_time = time_in_ms()
    actual_tiffs = []
    standardized_tiffs: List[FileTiff] = []

    for file in files:
        if is_tiff(file):
            actual_tiffs.append(file)
        else:
            get_log().info("standardising_file_not_tiff_skipped", file=file)

    gdal_version = get_gdal_version()
    get_log().info("standardising_start", gdalVersion=gdal_version, fileCount=len(actual_tiffs))

    with Pool(concurrency) as p:
        standardized_tiffs = p.map(partial(standardising, preset=preset), actual_tiffs)
        p.close()
        p.join()

    get_log().info("standardising_end", duration=time_in_ms() - start_time, fileCount=len(standardized_tiffs))

    return standardized_tiffs


def standardising(file: str, preset: str) -> FileTiff:
    get_log().info(f"standardising {file}", path=file)
    output_folder = "/tmp/"
    _, src_file_path = parse_path(file)
    standardized_file_name = f"{get_file_name_from_path(src_file_path)}.tiff"
    standardized_file_path = os.path.join(output_folder, standardized_file_name)
    command = get_gdal_command(preset)
    run_gdal(command, input_file=file, output_file=standardized_file_path)
    tiff = FileTiff(file)
    tiff.set_path_standardised(standardized_file_path)

    return tiff


def main() -> None:
    concurrency: int = 1
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser.parse_args()
    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    run_standardising(source, arguments.preset, concurrency)


if __name__ == "__main__":
    main()
