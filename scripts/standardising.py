import argparse
import os
import subprocess
import tempfile

from aws_helper import get_bucket, get_credentials, parse_path
from linz_logger import get_log

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source", required=True)
parser.add_argument("--destination", dest="destination", required=True)
arguments = parser.parse_args()
source = arguments.source
destination = arguments.destination

get_log().info("standardising", source=source, destination=destination)
dst_bucket_name, dst_path = parse_path(destination)
get_log().debug("destination", bucket=dst_bucket_name, file_path=dst_path)
dst_bucket = get_bucket(dst_bucket_name)

# TODO Include TDE-411 here
file_list = [source]

gdal_env = os.environ.copy()

for file in file_list:
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_bucket_name, src_file_path = parse_path(file)
        get_log().debug("processing_file", bucket=src_bucket_name, file_path=src_file_path)
        standardized_file_name = f"standardized_{os.path.basename(src_file_path)}"
        tmp_file_path = os.path.join(tmp_dir, standardized_file_name)
        src_gdal_path = file.replace("s3://", "/vsis3/")

        # Set the credentials for GDAL to be able to read the source file
        credentials = get_credentials(src_bucket_name)
        gdal_env["AWS_ACCESS_KEY_ID"] = credentials.access_key
        gdal_env["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
        gdal_env["AWS_SESSION_TOKEN"] = credentials.token

        # Run GDAL to standardized the file
        get_log().debug("run_gdal_translate", src=src_gdal_path, output=tmp_file_path)
        gdal_command = [
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
            src_gdal_path,
            tmp_file_path,
        ]
        try:
            proc = subprocess.run(gdal_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=gdal_env, check=True)
        except subprocess.CalledProcessError as cpe:
            get_log().error("run_gdal_translate_failed", command=" ".join(gdal_command))
            raise cpe
        get_log().debug("run_gdal_translate_succeded", command=" ".join(gdal_command))

        # Upload the standardized file to destination
        dst_file_path = os.path.join(dst_path, standardized_file_name).strip("/")
        get_log().debug("upload_file", path=dst_file_path)
        dst_bucket.upload_file(tmp_file_path, dst_file_path)
