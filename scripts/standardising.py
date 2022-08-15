import os
from typing import List

from linz_logger import get_log

from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import parse_source
from scripts.files.files_helper import get_file_name_from_path, is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.logging.time_helper import time_in_ms


def standardising(files: List[str]) -> List[str]:
    start_time = time_in_ms()
    output_folder = "/tmp/"
    output_files = []

    get_log().info("standardising_start", source=files)

    for file in files:
        if not is_tiff(file):
            get_log().info("standardising_file_not_tiff_skipped", file=file)
            continue

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
        output_files.append(tmp_file_path)

    get_log().info("standardising_end", source=files, duration=time_in_ms() - start_time)

    return output_files


def main() -> None:
    source = parse_source()
    standardising(source)


if __name__ == "__main__":
    main()
