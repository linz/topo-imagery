import json
import os
import sys
import tempfile
from collections import Counter
from typing import List

from linz_logger import get_log

# osgeo is embbed in the Docker image
from osgeo import gdal  # pylint: disable=import-error

from scripts.cli.cli_helper import parse_source
from scripts.files.files_helper import is_tiff
from scripts.files.fs import read, write
from scripts.logging.logging_keys import LOG_REASON_SKIP, LOG_REASON_START, LOG_REASON_SUCCESS, LOG_REASON_WARN
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


def create_polygons(files: List[str]) -> None:
    start_time = time_in_ms()
    output_files = []
    is_error = False

    get_log().info(
        "Create polygons started",
        action=create_polygons.__name__,
        source=files,
        reason=LOG_REASON_START,
    )

    for file in files:
        try:
            if not is_tiff(file):
                get_log().debug(
                    f"File: '{file}' is not a tiff. Polygon won't be created for this file",
                    action=create_polygons.__name__,
                    reason=LOG_REASON_SKIP,
                    path=file,
                )
                continue
            with tempfile.TemporaryDirectory() as tmp_dir:
                source_file_name = os.path.basename(file)
                tmp_file = os.path.join(tmp_dir, "temp.tif")

                # Get the file
                write(tmp_file, read(file))

                # Run create_mask
                mask_file = os.path.join(tmp_dir, "mask.tif")
                create_mask(tmp_file, mask_file)

                # Run create_polygon
                data_px_count = get_pixel_count(mask_file)
                if data_px_count == 0:
                    # exclude extents if tif is all white or black
                    get_log().warn(
                        f"data_px_count was zero in create_mask function for the tif {mask_file}",
                        action=create_polygons.__name__,
                        reason=LOG_REASON_WARN,
                        path=mask_file,
                    )
                else:
                    destination_file_name = os.path.splitext(source_file_name)[0] + ".geojson"
                    temp_file_path = os.path.join(tmp_dir, destination_file_name)
                    polygonize_command = f'gdal_polygonize.py -q "{mask_file}" "{temp_file_path}" -f GeoJSON'
                    os.system(polygonize_command)

                output_files.append(temp_file_path)
        except Exception as e:  # pylint:disable=broad-except
            get_log().error(
                f"An error occurs during polygon creation for the file: {file}",
                action=create_polygons.__name__,
                path=file,
                reason=LOG_REASON_SKIP,
                error=str(e),
            )
            is_error = True

    with open("/tmp/file_list.json", "w", encoding="utf-8") as jf:
        json.dump(output_files, jf)

    if is_error:
        get_log().warn(
            "Create polygons ended with at least one file skipped",
            action=create_polygons.__name__,
            reason=LOG_REASON_WARN,
            duration=time_in_ms() - start_time,
        )
        sys.exit(1)
    else:
        get_log().info(
            "Create polygons ended",
            action=create_polygons.__name__,
            source=files,
            reason=LOG_REASON_SUCCESS,
            duration=time_in_ms() - start_time,
        )


def main() -> None:
    create_polygons(parse_source)


if __name__ == "__main__":
    main()
