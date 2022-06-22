import argparse
import os
import subprocess
import tempfile

from linz_logger import get_log

import aws_helper

parser = argparse.ArgumentParser()
parser.add_argument('--source',dest='source', required=True)
parser.add_argument('--destination', dest='destination', required=True)
arguments = parser.parse_args()
source = arguments.source
destination = arguments.destination
#TODO if destination needs write permission we have to handle this

get_log().info("standardising", source=source, destination=destination)

src_bucket_name, src_file_path = aws_helper.parse_path(source)
dst_bucket_name, dst_path = aws_helper.parse_path(destination)
get_log().debug("source", bucket=src_bucket_name, file_path=src_file_path)
get_log().debug("destination", bucket=dst_bucket_name, file_path=dst_path)
dst_bucket = aws_helper.get_bucket(dst_bucket_name)

with tempfile.TemporaryDirectory() as tmp_dir:
    standardized_file_name = f"standardized_{os.path.basename(src_file_path)}"
    tmp_file_path = os.path.join(tmp_dir, standardized_file_name)
    src_gdal_path = f"/vsis3/{source.replace('s3://', '')}"

    # Set the credentials for GDAL to be able to read the source file
    credentials = aws_helper.get_credentials(src_bucket_name)
    gdal_env = os.environ.copy()
    gdal_env["AWS_ACCESS_KEY_ID"] = credentials.access_key
    gdal_env["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
    gdal_env["AWS_SESSION_TOKEN"] = credentials.token

    # Run GDAL to standardized the file
    get_log().debug("run_gdal_translate", src=src_gdal_path, output=tmp_file_path)
    command = ["gdal_translate", "-q", "-scale", "0", "255", "0", "254", "-a_srs", "EPSG:2193", "-a_nodata", "255", "-b", "1", "-b", "2", "-b", "3", "-co", "compress=lzw", src_gdal_path, tmp_file_path]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=gdal_env)
    if proc.returncode != 0:
        get_log().error("run_gdal_translate_failed", command=" ".join(command))
        raise Exception(proc.stderr.decode())
    get_log().debug("run_gdal_translate_succeded", command=" ".join(command))

    # Upload the standardized file to destination
    dst_file_path = os.path.join(dst_path, standardized_file_name).strip("/")
    get_log().debug("upload_file", path=dst_file_path)
    dst_bucket.upload_file(tmp_file_path, dst_file_path)
