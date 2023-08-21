import argparse
import json
import os
import tempfile
from typing import List

from linz_logger import get_log

from scripts.files.files_helper import get_file_name_from_path, is_GTiff, is_tiff
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_thumbnail_command
from scripts.logging.time_helper import time_in_ms


def thumbnails(tiff_list: List[str], target: str) -> int:
    """Generate a thumbnail `jpg` file for each tiff in `tiff_list`.
    GeoTIFF and TIFF (not georeferenced) thumbnails are generated differently.

    Args:
        tiff_list: list of tiffs
        target: output directory

    Returns:
        The number of thumbnails generated.
    """
    start_time = time_in_ms()
    get_log().info("thumbnails_start")
    count = 0

    with tempfile.TemporaryDirectory() as tmp_path:
        for file in tiff_list:
            if not is_tiff(file):
                get_log().debug("thumbnails_skip_not_tiff", file=file)
                continue

            basename = get_file_name_from_path(file)
            target_thumbnail = os.path.join(target, f"{basename}-thumbnail.jpg")
            # Verify the thumbnail has not been already generated
            if exists(target_thumbnail):
                get_log().info("thumbnails_already_exists", path=target_thumbnail)
                continue
            transitional_jpg = os.path.join(tmp_path, f"{basename}.jpg")
            tmp_thumbnail = os.path.join(tmp_path, f"{basename}-thumbnail.jpg")
            source_tiff = os.path.join(tmp_path, f"{basename}.tiff")
            # Download source file
            write(source_tiff, read(file))

            # Generate thumbnail
            # For both GeoTIFF and TIFF (not georeferences) this is done in 2 steps.
            # Why? because it hasn't been found another way to get the same visual aspect.
            if is_GTiff(source_tiff):
                get_log().info("thumbnail_generate_geotiff", path=target_thumbnail)
                run_gdal(get_thumbnail_command("jpeg", source_tiff, transitional_jpg, "50%", "50%"))
                run_gdal(get_thumbnail_command("jpeg", transitional_jpg, tmp_thumbnail, "30%", "30%"))
            else:
                get_log().info("thumbnail_generate_tiff", path=target_thumbnail)
                run_gdal(
                    get_thumbnail_command(
                        "jpeg", source_tiff, transitional_jpg, "50%", "50%", ["-srcwin", "1280", "730", "7140", "9950"]
                    )
                )
                run_gdal(get_thumbnail_command("jpeg", transitional_jpg, tmp_thumbnail, "30%", "30%"))

            # Upload to target
            write(target_thumbnail, read(tmp_thumbnail))
            count += 1

    get_log().info("thumbnails_end", count=count, duration=time_in_ms() - start_time)
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--target", dest="target", required=True, help="Output location path")
    arguments = parser.parse_args()
    from_file = arguments.from_file

    source = json.loads(read(from_file))
    # FIXME: multi processed that
    for tiff_list in source:
        thumbnails(tiff_list, arguments.target)


if __name__ == "__main__":
    main()
