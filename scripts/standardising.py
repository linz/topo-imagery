import argparse
import os
import tempfile

from aws_helper import get_bucket, parse_path
from file_helper import get_file_name_from_path
from format_source import format_source
from gdal_helper import run_gdal
from linz_logger import get_log

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source", nargs="+", required=True)
parser.add_argument("--destination", dest="destination", required=True)
arguments = parser.parse_args()
source = arguments.source
destination = arguments.destination

source = format_source(source)

get_log().info("standardising", source=source, destination=destination)
dst_bucket_name, dst_path = parse_path(destination)
get_log().debug("destination", bucket=dst_bucket_name, file_path=dst_path)
dst_bucket = get_bucket(dst_bucket_name)
gdal_env = os.environ.copy()

for file in source:
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_bucket_name, src_file_path = parse_path(file)
        standardized_file_name = f"standardized_{get_file_name_from_path(src_file_path)}"
        tmp_file_path = os.path.join(tmp_dir, standardized_file_name)

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
            "biggtiff=yes",
            "-co",
            "overview_resampling=lanczos",
            "-co",
            "blocksize=512",
            "-co",
            "overview_quality=90",
            "-co",
            "sparse_ok=true"
        ]
        run_gdal(command, input_file=file, output_file=tmp_file_path, input_file_index=17)

        # Upload the standardized file to destination
        dst_file_path = os.path.join(dst_path, standardized_file_name).strip("/")
        get_log().debug("upload_file", path=dst_file_path)
        dst_bucket.upload_file(tmp_file_path, dst_file_path)
