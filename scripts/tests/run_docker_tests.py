import argparse
import json
import os
import subprocess
import sys
import tempfile
from enum import Enum
from typing import List, NamedTuple, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, TileFiles, get_tile_files
from scripts.files.fs import read

docker_dir = "tests/data/"

class DataType(str, Enum):
    ALL = "all"
    AERIAL = "aerial"
    ELEVATION = "elevation"
    HISTORICAL = "historical"

class StandardisingArgs(NamedTuple):
    file: str
    preset: str
    extra_args: Optional[List[str]] = []

def get_preset(data_type: DataType) -> str:
    """Get the preset corresponding to the Data Type.

    Args:
        data_type: type of the data

    Returns:
        a preset
    """
    preset = "webp"
    if data_type == DataType.ELEVATION:
        preset = "dem_lerc"

    return preset

def get_standardising_args(data_type: DataType, test_file_suffix: str) -> List[StandardisingArgs]:
    standardising_args = []
    if data_type == DataType.ALL:
        for type_enum in DataType:
            if type_enum == DataType.ALL:
                continue
            standardising_args.extend(get_standardising_args(type_enum, test_file_suffix))
        return standardising_args

    standardising_args.append(StandardisingArgs(file=data_type + test_file_suffix, preset=get_preset(data_type)))
    if data_type == DataType.AERIAL:
        # Add the cutline test
        standardising_args.append(StandardisingArgs(file=data_type + test_file_suffix, preset=get_preset(data_type), extra_args=["--cutline", os.path.join(docker_dir, "cutline.fgb")]))
    return standardising_args


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', dest="type", choices=[DataType.ALL.value, DataType.AERIAL.value,DataType.ELEVATION.value, DataType.HISTORICAL.value], required=True, help="The data type to run the test on.")
    parser.add_argument('--aws', dest="is_aws", required=False, help="Runs the test using files stored on AWS S3.")
    arguments = parser.parse_args()

    data_type = arguments.type
    test_file_suffix = ".json"
    if arguments.is_aws:
        test_file_suffix = "_aws.json"
    local_dir = "scripts/tests/data/"

    # Build Docker
    subprocess.call("docker build -t topo-imagery-test .", shell=True)
    
    # Get the standardise_validate.py arguments
    standardising_args = get_standardising_args(data_type, test_file_suffix)

    for arg in standardising_args:
        with tempfile.TemporaryDirectory() as tmp_path:
            # Parse the input JSON file in order to test the output
            source = json.dumps(json.loads(read(os.path.join(local_dir, arg.file))))
            try:
                tile_files: List[TileFiles] = get_tile_files(source)
            except InputParameterError as e:
                get_log().error("An error occurred while getting tile_files", error=str(e))
                sys.exit(1)

            # Run standardise_validate.py with test file
            subprocess.call("docker run  -v {}:/tmp/ topo-imagery python3 standardise_validate.py --from-file {} --preset {} --target-epsg 2193 --source-epsg 2193 --target /tmp/ --collection-id 123 --start-datetime 2023-01-01 --end-datetime 2023-01-01 {}".format(tmp_path, os.path.join(docker_dir, arg.file), arg.preset, " ".join(arg.extra_args)), shell=True)

            # Verify output(s)
            for tile in tile_files:
                output_file = f"{tile.output}.tiff"
                subprocess.call(f"cmp --silent {os.path.join(tmp_path, output_file)} {os.path.join(local_dir, 'output', output_file)}", shell=True)

