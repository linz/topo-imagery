import argparse
import os
import sys
import tempfile

from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.cli.cli_helper import InputParameterError, load_input_files
from scripts.files.files_helper import get_file_name_from_path, is_GTiff, is_tiff
from scripts.gdal.gdal_helper import get_vfs_path, run_gdal
from scripts.gdal.gdal_preset import get_thumbnail_command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--target", dest="target", required=True, help="Output location path")
    arguments = parser.parse_args()
    print(arguments.source)

    with tempfile.TemporaryDirectory() as tmp_path:
        try:
            tile_files = load_input_files(arguments.from_file)
        except InputParameterError as e:
            get_log().error("An error occurred when loading the input file.", error=str(e))
            sys.exit(1)

        for tile in tile_files:
            if len(tile.inputs) > 1:
                get_log().error("Found more than 1 input file per tile.", count=len(tile.inputs))
                sys.exit(1)

            file = tile.inputs[0]
            if not is_tiff(file):
                get_log().debug("Not Tiff File Skipped", file=file)
                continue

            basename = get_file_name_from_path(file)
            tmp_target = os.path.join(tmp_path, f"{basename}-thumbnail.jpg")
            target = os.path.join(arguments.target, f"{basename}-thumbnail.jpg")
            if is_s3(file):
                file = get_vfs_path(file)

            if is_GTiff(file):
                get_log().info("Creating thumbnail GeoTIFF thumbnail", path=target)
                run_gdal(get_thumbnail_command("jpeg", file, tmp_target, "50%", "50%"))
                run_gdal(get_thumbnail_command("jpeg", tmp_target, target, "30%", "30%"))
            else:
                get_log().info("Creating thumbnail TIFF thumbnail", path=target)
                run_gdal(
                    get_thumbnail_command("jpeg", file, tmp_target, "50%", "50%", ["-srcwin", "1280", "730", "7140", "9950"])
                )
                run_gdal(get_thumbnail_command("jpeg", tmp_target, target, "30%", "30%"))


if __name__ == "__main__":
    main()
