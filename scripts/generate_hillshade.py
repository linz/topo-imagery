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
from scripts.gdal.gdal_presets import HillshadePreset
from scripts.logging.time_helper import time_in_ms
from scripts.standardising import create_vrt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file",
        dest="from_file",
        required=True,
        help="Specify the path to a json file containing the input tiffs. "
        "Format: [{'output': 'tile1', 'inputs': ['path/input1.tiff', 'path/input2.tiff']}]",
    )
    parser.add_argument(
        "--preset",
        dest="preset",
        required=True,
        choices=[preset.value for preset in HillshadePreset],
        help="Type of hillshade to generate.",
    )
    parser.add_argument("--target", dest="target", required=True, help="Specify the path to save the generated hillshade to.")
    parser.add_argument(
        "--force",
        dest="force",
        help="Regenerate the hillshade TIFF files if already exist. Defaults to False.",
        action="store_true",
    )

    return parser.parse_args()


def create_hillshade(
    tile: TileFiles,
    preset: str,
    target_output: str = "/tmp/",
    force: bool = False,
) -> str | None:
    """Create a hillshade TIFF file from a `TileFiles` which include an output tile with its input TIFFs.

    Args:
        tile: a TileFiles object with the input TIFFs and the output tile name.
        preset: a `HillshadePreset` to use. See `gdal.gdal_presets.py`.
        target_output: path where the output files need to be saved to. Defaults to "/tmp/".
        force: overwrite existing output file. Defaults to False.

    Returns:
        The filename of the hillshade TIFF file if created.
    """
    hillshade_file_name = tile.output + ".tiff"
    hillshade_with_stats_file_name = tile.output + "_w_stats.tiff"

    hillshade_file_path = os.path.join(target_output, hillshade_file_name)

    # Already processed can skip processing
    if exists(hillshade_file_path):
        if not force:
            get_log().info("Skipping: hillshade TIFF already exists.", path=hillshade_file_path)
            return None
        get_log().info("Overwriting: hillshade TIFF already exists.", path=hillshade_file_path)

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:
        hillshade_working_path = os.path.join(tmp_path, hillshade_file_name)
        hillshade_with_stats_working_path = os.path.join(tmp_path, hillshade_with_stats_file_name)

        source_files = write_all(tile.inputs, f"{tmp_path}/source/")
        source_tiffs = [file for file in source_files if is_tiff(file)]

        # Start from base VRT
        input_file = create_vrt(source_tiffs, tmp_path)

        # Need GDAL to write to temporary location so no broken files end up in the final folder.
        run_gdal(get_hillshade_command(preset), input_file=input_file, output_file=hillshade_working_path)

        # Add statistics to the TIFF
        run_gdal(
            ["gdal_translate", "-stats"], input_file=hillshade_working_path, output_file=hillshade_with_stats_working_path
        )

        write(hillshade_file_path, read(hillshade_with_stats_working_path), content_type=ContentType.GEOTIFF.value)

        return hillshade_file_path


def run_create_hillshade(
    todo: list[TileFiles],
    preset: str,
    concurrency: int,
    target_output: str = "/tmp/",
    force: bool = False,
) -> list[str]:
    """Run `create_hillshade()` in parallel (see `concurrency`).

    Args:
        todo: list of TileFiles (tile name and input files) to hillshade
        preset: `HillshadePreset` to use. See `gdal.gdal_presets.py`
        concurrency: number of concurrent tiles to process
        target_output: output directory path. Defaults to "/tmp/"
        force: overwrite existing files. Defaults to False.

    Returns:
        the list of generated hillshade TIFF paths.
    """
    with Pool(concurrency) as p:
        results = [
            entry
            for entry in p.map(
                partial(
                    create_hillshade,
                    preset=preset,
                    target_output=target_output,
                    force=force,
                ),
                todo,
            )
            if entry is not None
        ]
        p.close()
        p.join()

    return results


def main() -> None:
    start_time = time_in_ms()
    arguments = parse_args()

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    get_log().info(
        "generate_hillshade_start", gdalVersion=os.environ["GDAL_VERSION"], fileCount=len(tile_files), preset=arguments.preset
    )

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    file_paths = run_create_hillshade(tile_files, arguments.preset, concurrency, arguments.target, arguments.force)

    get_log().info(
        "generate_hillshade_end", duration=time_in_ms() - start_time, fileCount=len(file_paths), path=arguments.target
    )


if __name__ == "__main__":
    main()
