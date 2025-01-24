import argparse
import os
import sys
import tempfile
from datetime import datetime, timezone
from functools import partial
from multiprocessing import Pool

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, TileFiles, is_argo, load_input_files, valid_date
from scripts.datetimes import RFC_3339_DATETIME_FORMAT, format_rfc_3339_nz_midnight_datetime_string
from scripts.files.files_helper import SUFFIX_JSON, ContentType, is_tiff
from scripts.files.fs import exists, read, write, write_all
from scripts.gdal.gdal_commands import get_hillshade_command
from scripts.gdal.gdal_helper import gdal_info, run_gdal
from scripts.gdal.gdal_presets import HillshadePreset
from scripts.json_codec import dict_to_json_bytes
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.create_stac import create_item
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
        choices=[preset.value for preset in HillshadePreset],
        help="Type of hillshade to generate.",
    )
    parser.add_argument("--target", dest="target", required=True, help="The path to save the generated hillshade to.")
    parser.add_argument("--collection-id", dest="collection_id", help="Unique id for collection", required=True)
    parser.add_argument(
        "--start-datetime",
        dest="start_datetime",
        help="Start datetime in format YYYY-MM-DD. Only optional if includeDerived.",
        type=valid_date,
    )
    parser.add_argument(
        "--end-datetime",
        dest="end_datetime",
        help="End datetime in format YYYY-MM-DD. Only optional if includeDerived.",
        type=valid_date,
    )
    parser.add_argument(
        "--current-datetime",
        dest="current_datetime",
        help=(
            "The datetime to be used as current datetime in the metadata. "
            "Format: RFC 3339 UTC datetime, `YYYY-MM-DDThh:mm:ssZ`."
        ),
        required=False,
        default=datetime.now(timezone.utc).strftime(RFC_3339_DATETIME_FORMAT),
    )

    return parser.parse_args()


def create_hillshade(
    files: TileFiles,
    preset: str,
    target_output: str = "/tmp/",
) -> str | None:
    """Create a hillshade TIFF file from a `TileFiles` which include an output tile with its input TIFFs.

    Args:
        files: a TileFiles object with the input TIFFs and the output tile name.
        preset: a `HillshadePreset` to use. See `gdal.gdal_presets.py`.
        target_output: path where the output files need to be saved to. Defaults to "/tmp/".

    Returns:
        The filename of the hillshade TIFF file if created.
    """
    hillshade_file_name = files.output + ".tiff"

    hillshade_file_path = os.path.join(target_output, hillshade_file_name)

    # Already processed can skip processing
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

        # Need GDAL to write to temporary location so no broken files end up in the final folder.
        run_gdal(get_hillshade_command(preset), input_file=input_file, output_file=hillshade_working_path)

        write(hillshade_file_path, read(hillshade_working_path), content_type=ContentType.GEOTIFF.value)

        return hillshade_file_path


def run_create_hillshade(
    todo: list[TileFiles],
    preset: str,
    concurrency: int,
    gdal_version: str,
    target_output: str = "/tmp/",
) -> list[str]:
    """Run `create_hillshade()` in parallel (`concurrency`).

    Args:
        todo: list of TileFiles (tile name and input files) to hillshade
        preset: `HillshadePreset` to use. See `gdal.gdal_presets.py`
        concurrency: number of concurrent files to process
        gdal_version: version of GDAL used
        target_output: output directory path. Defaults to "/tmp/"

    Returns:
        Nothing
    """
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


def main() -> None:
    arguments = parse_args()

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    file_paths = run_create_hillshade(tile_files, arguments.preset, concurrency, os.environ["GDAL_VERSION"], arguments.target)

    start_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.start_datetime)
    end_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.end_datetime)
    for path in file_paths:
        if path is None:
            continue
        # Create STAC and save in target
        item = create_item(
            path,
            start_datetime,
            end_datetime,
            arguments.collection_id,
            os.environ["GDAL_VERSION"],
            arguments.current_datetime,
            gdal_info(path),
        )
        stac_item_path = path.rsplit(".", 1)[0] + SUFFIX_JSON
        write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)


if __name__ == "__main__":
    main()
