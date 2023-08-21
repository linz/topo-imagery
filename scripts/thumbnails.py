import argparse
import os
import sys
import tempfile

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, load_input_files
from scripts.files.files_helper import get_file_name_from_path, is_GTiff, is_tiff
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_thumbnail_command
from scripts.logging.time_helper import time_in_ms


def main() -> None:
    start_time = time_in_ms()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--target", dest="target", required=True, help="Output location path")
    arguments = parser.parse_args()
    from_file = arguments.from_file
    count = 0

    get_log().info("thumbnails_start", input=from_file)

    with tempfile.TemporaryDirectory() as tmp_path:
        try:
            tile_files = load_input_files(from_file)
        except InputParameterError as e:
            get_log().error("thumbnails_input_error", error=str(e))
            sys.exit(1)

        for tile in tile_files:
            # Verify 1 input for 1 output
            if len(tile.inputs) > 1:
                get_log().error("thumbnails_too_many_input_files", output=tile.output, count=len(tile.inputs))
                continue

            file = tile.inputs[0]
            if not is_tiff(file):
                get_log().debug("thumbnails_skip_not_tiff", file=file)
                continue

            basename = get_file_name_from_path(file)
            target_thumbnail = os.path.join(arguments.target, f"{basename}-thumbnail.jpg")
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


if __name__ == "__main__":
    main()
