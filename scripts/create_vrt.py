import argparse
import json
import os

from scripts.files.files_helper import flatten_file_list, convert_s3_paths
from scripts.standardising import create_vrt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--target", dest="target", help="Target output", required=True)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    os.environ.__setitem__("AWS_NO_SIGN_REQUEST", "TRUE")
    # ToDo: gdalbuildvrt does not properly handle/read environment variables.
    # This currently leads to an error being unable to access any files in s3 through /vsis3/.
    # May need fixing in how gdal is called in gdal_helper.py / run_gdal().

    source_files = json.load(arguments.from_file)
    source_files = convert_s3_paths(flatten_file_list(source_files))

    create_vrt(source_tiffs=source_files, target_path=arguments.target, add_alpha=False)


if __name__ == "__main__":
    main()
