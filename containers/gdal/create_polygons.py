import argparse
import os
import tempfile
from collections import Counter
from urllib.parse import urlparse

import aws_helper
from linz_logger import get_log
from osgeo import gdal

parser = argparse.ArgumentParser()
parser.add_argument('--uri', dest='uri', required=True)
parser.add_argument('--destination', dest='destination', required=True)

arguments = parser.parse_args()

uri = arguments.uri
dest_bucket = arguments.destination

def create_mask(filepath, mask_dst):
    set_srs_command = f'gdal_edit.py -a_srs EPSG:2193 "{filepath}"'
    os.system(set_srs_command)
    calc_command = (
        f"gdal_calc.py "
        f"--quiet "
        f'-A "{filepath}" --A_band=1 '
        f'--outfile="{mask_dst}" '
        f'--calc "255*logical_or(((A==254)*(A==254)*(A==254)),((A==0)*(A==0)*(A==0)))" '
        f"--NoDataValue=255 "
        f'--co="compress=lzw"'
    )
    os.system(calc_command)

def get_pixel_count(filepath):
    data_pixels_count = 0
    dataset = gdal.Open(filepath)
    array = dataset.ReadAsArray()
    counter_counts = Counter(array.flatten())
    for pixel_value, count in counter_counts.items():
        if pixel_value != 255:
            data_pixels_count += count
    return data_pixels_count

with tempfile.TemporaryDirectory() as tmp_dir:
    file_name = os.path.basename(uri)
    # Download the file
    if str(uri).startswith("s3://"):
        uri_parse = urlparse(uri, allow_fragments=False)
        bucket_name = uri_parse.netloc
        bucket = aws_helper.get_bucket(bucket_name)
        uri = os.path.join(tmp_dir, "temp.tif")
        get_log().debug("download_file", source=uri_parse.path[1:], bucket=bucket_name, dest=uri, fileName=file_name)
        bucket.download_file(uri_parse.path[1:], uri)


    # Run create_mask=
    get_log().debug("create_mask", source=uri_parse.path[1:], bucket=bucket_name, dest=uri)
    mask_file = os.path.join(tmp_dir, "mask.tif")
    create_mask(uri, mask_file)
    gdal_info_command = ("gdalinfo " + os.path.join(tmp_dir, "mask.tif") + " -json")
    os.system(gdal_info_command)

    # Run create_polygon
    data_px_count = get_pixel_count(mask_file)
    if data_px_count == 0:
        # exclude extents if tif is all white or black
        get_log().debug(f"- data_px_count was zero in create_mask function for the tif {mask_file}")
    else:
        poly_dst = os.path.join(tmp_dir, f"{file_name}.geojson")
        polygonize_command = f'gdal_polygonize.py -q "{mask_file}" "{poly_dst}" -f GeoJSON'
        os.system(polygonize_command)

        # Upload shape file
        destination = aws_helper.get_bucket(dest_bucket)
        destination.upload_file(poly_dst, f"{file_name}.geojson")
