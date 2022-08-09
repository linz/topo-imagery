import os

from aws_helper import parse_path
from cli_helper import parse_source
from file_helper import get_file_name_from_path, is_tiff
from gdal_helper import run_gdal
from linz_logger import get_log
from time_helper import time_in_ms

start_time = time_in_ms()

source = parse_source()

get_log().info("standardising_start", source=source)

gdal_env = os.environ.copy()

for file in source:
    if not is_tiff(file):
        get_log().trace("standardising_file_not_tiff_skipped", file=file)
        continue

    src_bucket_name, src_file_path = parse_path(file)
    standardized_file_name = f"standardized_{get_file_name_from_path(src_file_path)}"
    tmp_file_path = os.path.join("/tmp/", standardized_file_name)
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

    get_log().info("standardising_end", source=source, duration=time_in_ms() - start_time)
