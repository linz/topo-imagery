import argparse
import json
import os
import tempfile
from collections import Counter
from urllib.parse import urlparse

from aws_helper import download_s3_file, get_bucket, is_s3
from format_source import format_source
from gdal_helper import run_gdal
from linz_logger import get_log

# osgeo is embbed in the Docker image
from osgeo import gdal  # pylint: disable=import-error


def create_mask(file_path: str, mask_dst: str) -> None:
    set_srs_command = ["gdal_edit.py", "-a_srs", "EPSG:2193"] 
    run_gdal(set_srs_command, input_file=file_path)

    calc_command = [
        "gdal_calc.py",
        "--quiet",
        "-A",
        file_path,
        "--A_band=1",
        f"--outfile={mask_dst}",
        "--calc",
        "255*logical_or(((A==254)*(A==254)*(A==254)),((A==0)*(A==0)*(A==0)))",
        "--NoDataValue=255",
        "--co=compress=lzw"
    ] # TODO: input and output files should be separated but they can't just be appended at end of command like others
    run_gdal(calc_command)


def get_pixel_count(file_path: str) -> int:
    data_pixels_count = 0
    dataset = gdal.Open(file_path)
    array = dataset.ReadAsArray()
    counter_counts = Counter(array.flatten())
    for pixel_value, count in counter_counts.items():
        if pixel_value != 255:
            data_pixels_count += count
    return data_pixels_count


def main() -> None:  # pylint: disable=too-many-locals
    logger = get_log()

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser.parse_args()
    source = arguments.source

    source = format_source(source)
    output_files = []

    for file in source:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_file_name = os.path.basename(file)

            # Download the file
            if is_s3(file):
                file, bucket_name = download_s3_file(file, tmp_dir, source_file_name)

            # Run create_mask
            get_log().debug("create_mask", source=source_file_name, bucket=bucket_name, destination=file)
            mask_file = os.path.join(tmp_dir, "mask.tif")
            create_mask(file, mask_file)

            # Run create_polygon
            data_px_count = get_pixel_count(mask_file)
            if data_px_count == 0:
                # exclude extents if tif is all white or black
                get_log().debug(f"- data_px_count was zero in create_mask function for the tif {mask_file}")
            else:
                destination_file_name = os.path.splitext(source_file_name)[0] + ".geojson"
                temp_file_path = os.path.join(tmp_dir, destination_file_name)
                polygonize_command = ["gdal_polygonize.py", "-q", mask_file, temp_file_path, "-f", "GeoJSON"]
                run_gdal(polygonize_command)

            output_files.append(temp_file_path)

    with open("/tmp/file_list.json", "w", encoding="utf-8") as jf:
        json.dump(output_files, jf)


if __name__ == "__main__":
    main()
