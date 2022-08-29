import os
from functools import partial
from multiprocessing import Pool
from typing import List

from linz_logger import get_log

from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import parse_source
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_gdal_command
from scripts.logging.time_helper import time_in_ms


def start_standardising(files: List[str], preset: str, concurrency: int) -> List[str]:
    start_time = time_in_ms()
    tiff_files = []
    output_files = []

    get_log().info("standardising_start", source=files)

    for file in files:
        if is_tiff(file):
            tiff_files.append(file)
        else:
            get_log().info("standardising_file_not_tiff_skipped", file=file)

    with Pool(concurrency) as p:
        output_files = p.map(partial(standardising, preset=preset), tiff_files)
        p.close()
        p.join()

    get_log().info("standardising_end", source=files, duration=time_in_ms() - start_time)

    return output_files


def standardising(file: str, preset: str) -> str:
    output_folder = "/tmp/"

    get_log().info("standardising_start", source=file)

    _, src_file_path = parse_path(file)
    standardized_file_name = f"{get_file_name_from_path(src_file_path)}.tiff"
    tmp_file_path = os.path.join(output_folder, standardized_file_name)

    command = get_gdal_command(preset)
    run_gdal(command, input_file=file, output_file=tmp_file_path)

    return tmp_file_path


def main() -> None:

    source = parse_source()
    start_standardising(source, "lzw", 1)

if __name__ == "__main__":
    main()
