import argparse
import os
import tempfile

from typing import List
from scripts.aws.aws_helper import is_s3
from scripts.gdal.gdal_preset import COMPRESS_LZW

from scripts.files.files_helper import is_GTiff, is_tiff
from linz_logger import get_log
from scripts.gdal.gdal_helper import run_gdal


def main() -> None:
    parser = argparse.ArgumentParser()
    # TODO what is source going to be?
    parser.add_argument("--source", dest="source", required=True, nargs="+", help="Source list of files")
    parser.add_argument("--target", dest="target", required=True, help="Output location path")
    arguments = parser.parse_args()
    print(arguments.source)

    with tempfile.TemporaryDirectory() as tmp_path:
        for file in arguments.source:
            if not is_tiff(file):
                get_log().debug("Not Tiff File Skipped", file=file)

            basename = os.path.splitext(os.path.basename(file))[0]
            tmp_target = os.path.join(tmp_path, f"{basename}-thumbnail.jpg")
            target = os.path.join(arguments.target, f"{basename}-thumbnail.jpg")
            if is_s3(file):
                file = file.replace("s3://", "/vsis3/")

            if is_GTiff(file):
                print(file)
                run_gdal(_thumbnail_command("jpeg", file, tmp_target, "50%", "50%", COMPRESS_LZW))
                run_gdal(_thumbnail_command("jpeg", tmp_target, target, "30%", "30%"))

            run_gdal(
                _thumbnail_command(
                    "jpeg", file, tmp_target, "50%", "50%", COMPRESS_LZW + ["-srcwin", "1280", "730", "7140", "9950"]
                )
            )
            run_gdal(_thumbnail_command("jpeg", tmp_target, target, "30%", "30%"))


def _thumbnail_command(
    compression: str, input: str, output: str, xsize: str, ysize: str, extra_args: List[str] = []
) -> List[str]:
    return [
        "gdal_translate",
        "-of",
        compression,
        "-b",
        "1",
        "-b",
        "2",
        "-b",
        "3",
        input,
        output,
        "-outsize",
        xsize,
        ysize,
    ] + extra_args


if __name__ == "__main__":
    main()
