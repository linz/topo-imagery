import argparse
import os
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial
from multiprocessing import Pool

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, TileFiles, is_argo, load_input_files, str_to_gsd
from scripts.datetimes import RFC_3339_DATETIME_FORMAT
from scripts.files.files_helper import SUFFIX_JSON, ContentType, is_tiff
from scripts.files.fs import exists, read, write, write_all
from scripts.gdal.gdal_commands import get_hillshade_command
from scripts.gdal.gdal_footprint import SUFFIX_FOOTPRINT, create_footprint
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_presets import HillshadePreset
from scripts.json_codec import dict_to_json_bytes
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.create_stac import create_item
from scripts.standardising import create_vrt


def get_args_parser() -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--collection-id",
        dest="collection_id",
        help="Unique id of the Collection. If not provided, STAC Items won't be created.",
    )
    parser.add_argument("--gsd", dest="gsd", type=str_to_gsd, required=False, help="GSD of imagery Dataset, for example 1")
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
    parser.add_argument("--target", dest="target", required=True, help="Specify the path to save the generated hillshade to.")
    parser.add_argument(
        "--force",
        dest="force",
        help="Regenerate the hillshade TIFF files if already exist. Defaults to False.",
        action="store_true",
    )

    return parser


def create_hillshade(
    tile: TileFiles,
    preset: str,
    target_output: str = "/tmp/",
    gsd: Decimal | None = None,
    force: bool = False,
) -> tuple[str, list[str]] | None:
    """Create a hillshade TIFF file from a `TileFiles` which include an output tile with its input TIFFs.

    Args:
        tile: a TileFiles object with the input TIFFs and the output tile name.
        preset: a `HillshadePreset` to use. See `gdal.gdal_presets.py`.
        target_output: path where the output files need to be saved to. Defaults to "/tmp/".
        gsd: Ground Sample Distance in meters. If provided, footprint will be created. Defaults to None.
        force: overwrite existing output file. Defaults to False.

    Returns:
        The filename of the hillshade TIFF file if created and the path of the input files used to create it.
    """
    hillshade_file_name = tile.output + ".tiff"
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

        source_files = write_all(tile.inputs, f"{tmp_path}/source/")
        source_tiffs = [file for file in source_files if is_tiff(file)]

        # Start from base VRT
        input_file = create_vrt(source_tiffs, tmp_path)

        # Need GDAL to write to temporary location so no broken files end up in the final folder.
        run_gdal(get_hillshade_command(preset), input_file=input_file, output_file=hillshade_working_path)

        write(hillshade_file_path, read(hillshade_working_path), content_type=ContentType.GEOTIFF.value)

        if gsd:
            footprint_tmp_path = create_footprint(hillshade_working_path, target_output, gsd)  # noqa: F821
            footprint_file_name = tile.output + SUFFIX_FOOTPRINT
            footprint_file_path = os.path.join(target_output, footprint_file_name)
            write(footprint_file_path, read(footprint_tmp_path), content_type=ContentType.GEOJSON.value)

        return hillshade_file_path, tile.inputs


def run_create_hillshade(
    todo: list[TileFiles],
    preset: str,
    concurrency: int,
    target_output: str = "/tmp/",
    force: bool = False,
) -> list[tuple[str, list[str]]]:
    """Run `create_hillshade()` in parallel (see `concurrency`).

    Args:
        todo: list of TileFiles (tile name and input files) to hillshade
        preset: `HillshadePreset` to use. See `gdal.gdal_presets.py`
        concurrency: number of concurrent tiles to process
        target_output: output directory path. Defaults to "/tmp/"
        force: overwrite existing files. Defaults to False.

    Returns:
        the list of generated hillshade TIFF paths with their input files.
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
    arguments_parser = get_args_parser()
    arguments = arguments_parser.parse_args()

    if arguments.collection_id and not arguments.gsd:
        arguments_parser.error("--gsd is required when --collection-id is provided, in order to generate Item footprints.")

    try:
        tile_files = load_input_files(arguments.from_file)
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    gdal_version = os.environ["GDAL_VERSION"]

    get_log().info("generate_hillshade_start", gdalVersion=gdal_version, fileCount=len(tile_files), preset=arguments.preset)

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    tiles = run_create_hillshade(tile_files, arguments.preset, concurrency, arguments.target, arguments.force)

    if arguments.collection_id:
        for path, derived_from_tiffs in tiles:
            if path is None:
                continue
            # Create STAC and save in target
            item = create_item(
                asset_path=path,
                start_datetime="",
                end_datetime="",
                collection_id=arguments.collection_id,
                gdal_version=gdal_version,
                current_datetime=arguments.current_datetime,
                gdalinfo_result=None,
                derived_from=[url_derived_from.rsplit(".", 1)[0] + ".json" for url_derived_from in derived_from_tiffs],
            )
            stac_item_path = path.rsplit(".", 1)[0] + SUFFIX_JSON
            write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)
    else:
        get_log().warning("No collection ID provided. Skipping STAC creation.")

    get_log().info("generate_hillshade_end", duration=time_in_ms() - start_time, fileCount=len(tiles), path=arguments.target)


if __name__ == "__main__":
    main()
