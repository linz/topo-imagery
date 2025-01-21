import argparse
import os
import sys
import tempfile
from functools import partial
from multiprocessing import Pool

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, TileFiles, is_argo, load_input_files
from scripts.files.files_helper import ContentType, is_tiff
from scripts.files.fs import exists, read, write, write_all
from scripts.gdal.gdal_commands import get_hillshade_command
from scripts.gdal.gdal_helper import run_gdal
from scripts.logging.time_helper import time_in_ms
from scripts.standardising import create_vrt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument(
        "--preset",
        dest="preset",
        required=True,
        help="Type of hillshade to generate. Example: 'multidirectional'",
    )
    parser.add_argument("--target", dest="target", required=True, help="The path to save the generated hillshade to.")

    return parser.parse_args()


def create_hillshade(
    files: TileFiles,
    preset: str,
    target_output: str = "/tmp/",
) -> str:
    hillshade_file_name = files.output + ".tiff"

    hillshade_file_path = os.path.join(target_output, hillshade_file_name)

    # Already proccessed can skip processing
    if exists(hillshade_file_path):
        get_log().info("hillshade_tiff_already_exists", path=hillshade_file_path)
        return None

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:
        hillshade_working_path = os.path.join(tmp_path, hillshade_file_name)
        source_files = write_all(files.inputs, f"{tmp_path}/source/")
        source_tiffs = [file for file in source_files if is_tiff(file)]

        # Start from base VRT
        input_file = create_vrt(source_tiffs, tmp_path)

        command = get_hillshade_command(preset)

        # Need GDAL to write to temporary location so no broken files end up in the done folder.
        run_gdal(command, input_file=input_file, output_file=hillshade_working_path)

        write(hillshade_file_path, read(hillshade_working_path), content_type=ContentType.GEOTIFF.value)
        return hillshade_file_path


def run_create_hillshade(
    todo: list[TileFiles],
    preset: str,
    concurrency: int,
    gdal_version: str,
    target_output: str = "/tmp/",
) -> None:
    """Run `create_hillshade()` in parallel (`concurrency`).

    Args:
        todo: list of TileFiles (tile name and input files) to hillshade
        preset: hillshade preset to use. See `gdal.gdal_preset.py`
        concurrency: number of concurrent files to process
        gdal_version: version of GDAL used for creating hillshades
        target_output: output directory path. Defaults to "/tmp/"

    Returns:
        Nothing
    """
    # pylint: disable-msg=too-many-arguments
    start_time = time_in_ms()

    get_log().info("create_hillshade_start", gdalVersion=gdal_version, fileCount=len(todo))

    with Pool(concurrency) as p:
        results = [
            entry
            for entry in p.map(
                partial(
                    create_hillshade,
                    preset=preset,
                    target_output=target_output,
                ),
                todo,
            )
            if entry is not None
        ]
        p.close()
        p.join()

    get_log().info("create_hillshade_end", duration=time_in_ms() - start_time, fileCount=len(results))

    return results


def main():
    arguments = parse_args()

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    run_create_hillshade(tile_files, arguments.preset, concurrency, os.environ["GDAL_VERSION"], arguments.target)


if __name__ == "__main__":
    main()
