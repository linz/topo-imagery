import argparse
import os
import tempfile
from collections import Counter
from urllib.parse import urlparse

from linz_logger import get_log

# osgeo is embbed in the Docker image
from osgeo import gdal  # pylint: disable=import-error

from scripts.aws_helper import get_bucket

import aws_helper as aws_helper

logger = get_log()

parser = argparse.ArgumentParser()
parser.add_argument("--uri", dest="uri", required=True)
parser.add_argument("--destination", dest="destination", required=True)
arguments = parser.parse_args()
uri = arguments.uri
destination = arguments.destination

# Split the s3 destination path
destination_bucket_name = aws_helper.bucket_name_from_path(destination)
destination_path = destination.replace("s3://", "").replace(f"{destination_bucket_name}/", "")


def create_mask(file_path: str, mask_dst: str) -> None:
    set_srs_command = f'gdal_edit.py -a_srs EPSG:2193 "{file_path}"'
    os.system(set_srs_command)
    calc_command = (
        f"gdal_calc.py "
        f"--quiet "
        f'-A "{file_path}" --A_band=1 '
        f'--outfile="{mask_dst}" '
        f'--calc "255*logical_or(((A==254)*(A==254)*(A==254)),((A==0)*(A==0)*(A==0)))" '
        f"--NoDataValue=255 "
        f'--co="compress=lzw"'
    )
    os.system(calc_command)


def get_pixel_count(file_path: str) -> int:
    data_pixels_count = 0
    dataset = gdal.Open(file_path)
    array = dataset.ReadAsArray()
    counter_counts = Counter(array.flatten())
    for pixel_value, count in counter_counts.items():
        if pixel_value != 255:
            data_pixels_count += count
    return data_pixels_count


with tempfile.TemporaryDirectory() as tmp_dir:
    source_file_name = os.path.basename(uri)
    # Download the file
    if str(uri).startswith("s3://"):
        uri_parse = urlparse(uri, allow_fragments=False)
        bucket_name = uri_parse.netloc
        bucket = get_bucket(bucket_name)
        uri = os.path.join(tmp_dir, "temp.tif")
        logger.debug("download_file", source=uri_parse.path[1:], bucket=bucket_name, destination=uri, sourceFileName=source_file_name)
        bucket.download_file(uri_parse.path[1:], uri)

    # Run create_mask
    logger.debug("create_mask", source=uri_parse.path[1:], bucket=bucket_name, destination=uri)
    mask_file = os.path.join(tmp_dir, "mask.tif")
    create_mask(uri, mask_file)

    # Run create_polygon
    data_px_count = get_pixel_count(mask_file)
    if data_px_count == 0:
        # exclude extents if tif is all white or black
        logger.debug(f"- data_px_count was zero in create_mask function for the tif {mask_file}")
    else:
        destination_file_name = os.path.splitext(source_file_name)[0] + ".geojson"
        temp_file_path = os.path.join(tmp_dir, destination_file_name)
        polygonize_command = f'gdal_polygonize.py -q "{mask_file}" "{temp_file_path}" -f GeoJSON'
        os.system(polygonize_command)

        # Upload shape file
        destination = get_bucket(dest_bucket)
        destination_file_path = os.path.join(destination_path, destination_file_name)
        logger.debug("upload_start", destinationBucket=destination_bucket_name, destinationFile=destination_file_path)
        try:
            destination_bucket.upload_file(temp_file_path, destination_file_path)
        except Exception as e:
            logger.debug("upload_error", err=e)
            raise e
        logger.debug("upload_end", destinationBucket=destination_bucket_name, destinationFile=destination_file_path)
