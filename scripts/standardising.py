import os
from multiprocessing import Pool
from typing import List

from linz_logger import get_log

from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import is_argo, parse_source
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.logging.time_helper import time_in_ms


def start_standardising(files: List[str], concurrency: int) -> List[str]:
    start_time = time_in_ms()
    tiff_files = []
    output_files = []

    get_log().info("standardising_start", source=files)

    for file in files:
        if is_tiff(file):
            tiff_files.append(file)
        else:
            get_log().info("standardising_file_not_tiff_skipped", file=file)

    if concurrency:
        with Pool(concurrency) as p:
            output_files = p.map(standardising, tiff_files)
            p.close()
            p.join()
    else:
        for tiff_file in tiff_files:
            output_files.append(standardising(tiff_file))

    get_log().info("standardising_end", source=files, duration=time_in_ms() - start_time)

    return output_files


def standardising(file: str) -> str:
    output_folder = "/tmp/"

    get_log().info("standardising_start", source=file)

    _, src_file_path = parse_path(file)
    standardized_file_name = f"standardized_{get_file_name_from_path(src_file_path)}"
    tmp_file_path = os.path.join(output_folder, standardized_file_name)

    command = [
        "gdal_translate",
        "-q",
        "-scale",
        "0",
        "255",
        "0",
        "254",
        "-a_srs",
        "EPSG:2193",
        "-a_nodata",
        "255",
        "-b",
        "1",
        "-b",
        "2",
        "-b",
        "3",
        "-of",
        "COG",
        "-co",
        "compress=lzw",
        "-co",
        "num_threads=all_cpus",
        "-co",
        "predictor=2",
        "-co",
        "overview_compress=webp",
        "-co",
        "bigtiff=yes",
        "-co",
        "overview_resampling=lanczos",
        "-co",
        "blocksize=512",
        "-co",
        "overview_quality=90",
        "-co",
        "sparse_ok=true",
    ]
    run_gdal(command, input_file=file, output_file=tmp_file_path)

    return tmp_file_path


def main() -> None:
    concurrency: int = 0
    source = parse_source()
    if is_argo():
        concurrency = 4
    start_standardising(source, concurrency)


if __name__ == "__main__":
    main()
