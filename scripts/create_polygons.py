import json
import os
import tempfile
from collections import Counter

from botocore.exceptions import ClientError
from linz_logger import get_log

# osgeo is embbed in the Docker image
from osgeo import gdal  # pylint: disable=import-error

from scripts.cli.cli_helper import parse_source
from scripts.files.files_helper import is_tiff
from scripts.files.fs import read, write
from scripts.logging.time_helper import time_in_ms


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


def main() -> None:
    start_time = time_in_ms()
    source = parse_source()
    output_files = []

    for file in source:
        if not is_tiff(file):
            get_log().trace("create_polygon_file_not_tiff_skipped", file=file)
            continue
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_file_name = os.path.basename(file)
            tmp_file = os.path.join(tmp_dir, "temp.tif")

            # Get the file
            write(tmp_file, read(file))
            file = tmp_file

            # Run create_mask
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
                polygonize_command = f'gdal_polygonize.py -q "{mask_file}" "{temp_file_path}" -f GeoJSON'
                os.system(polygonize_command)

            output_files.append(temp_file_path)

    with open("/tmp/file_list.json", "w", encoding="utf-8") as jf:
        json.dump(output_files, jf)

    get_log().info("create_polygons_end", source=source, duration=time_in_ms() - start_time)


if __name__ == "__main__":
    main()
