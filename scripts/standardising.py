import argparse
import os
import tempfile

from aws_helper import get_bucket, parse_path
from file_helper import get_file_name_from_path
from gdal_helper import run_gdal
from linz_logger import get_log

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source", required=True)
parser.add_argument("--destination", dest="destination", required=True)
arguments = parser.parse_args()
source = arguments.source
destination = arguments.destination

get_log().info("standardising", source=source, destination=destination)

src_bucket_name, src_file_path = parse_path(source)
dst_bucket_name, dst_path = parse_path(destination)
get_log().debug("source", bucket=src_bucket_name, file_path=src_file_path)
get_log().debug("destination", bucket=dst_bucket_name, file_path=dst_path)
dst_bucket = get_bucket(dst_bucket_name)

with tempfile.TemporaryDirectory() as tmp_dir:
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
        "-co",
        "compress=lzw",
    ]
    run_gdal(command, source, tmp_file_path)

    # Upload the standardized file to destination
    dst_file_path = os.path.join(dst_path, standardized_file_name).strip("/")
    get_log().debug("upload_file", path=dst_file_path)
    dst_bucket.upload_file(tmp_file_path, dst_file_path)
