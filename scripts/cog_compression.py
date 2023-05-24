import argparse
import csv
import os
from typing import Dict, List, NamedTuple

from linz_logger import get_log

from scripts.files.files_helper import is_tiff
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_build_vrt_command, get_custom_translate
from scripts.logging.time_helper import time_in_ms
from scripts.tile.tile_index import Bounds, Point, TileIndexException, get_bounds_from_name, get_tile_name


class Compression(NamedTuple):
    driver: str
    type: str
    predictor: int
    level: int


def compress(compression: Compression, input_file: str, tile_name: str, output_dir: str) -> List[str | float | int]:
    output_file_name = os.path.join(
        output_dir,
        f"{tile_name}_c-{compression.type}_p-{compression.predictor}_l-{compression.level}.{compression.driver}.tiff",
    )

    gdal_command = [
        "gdal_translate",
        "-of",
        compression.driver,
        input_file,
        output_file_name,
        "-co",
        "NUM_THREADS=ALL_CPUS",
        "-co",
        f"COMPRESS={compression.type}",
    ]
    if compression.predictor > 0:
        gdal_command += ["-co", f"PREDICTOR={compression.predictor}"]
    if compression.level > 0:
        gdal_command += ["-co", f"LEVEL={compression.level}"]

    start_time = time_in_ms()
    run_gdal(gdal_command)
    duration = time_in_ms() - start_time

    return [
        os.path.basename(output_file_name),
        compression.driver,
        compression.type,
        compression.predictor,
        compression.level,
        f"{os.path.getsize(output_file_name) / 1000000}",
        duration,
    ]


def format_file_name(file_name: str) -> str:
    # FIXME: This is very specific
    return file_name.replace("DEM_", "").replace("2021_", "")


def retile(files: List[str], target_scale: int, output_path: str, starts_with: str = "") -> List[str]:
    new_tiles: Dict[str, List[str]] = {}
    for file_path in files:
        if not os.path.isfile(file_path) or not is_tiff(file_path):
            continue
        formatted_file_path = format_file_name(file_path)
        file_name = os.path.basename(formatted_file_path)
        origin: Point = get_bounds_from_name(file_name).point
        try:
            outter_tile_name = get_tile_name(origin=origin, grid_size=target_scale)
        except TileIndexException:
            get_log().error("Cannot get tile_name", path=formatted_file_path, origin=origin)
            continue
        if not outter_tile_name.startswith(starts_with):
            continue
        if outter_tile_name not in new_tiles:
            new_tiles[outter_tile_name] = []
        new_tiles[outter_tile_name].append(file_path)

    output_files = []
    for output_tile, inner_files in new_tiles.items():
        # Create output directory per tile
        output_dir = os.path.join(output_path, output_tile)
        os.makedirs(output_dir, mode=0o777, exist_ok=True)

        # Create the `vrt` file
        vrt_path = os.path.join(output_dir, f"{output_tile}.vrt")
        run_gdal(command=get_build_vrt_command(files=inner_files, output=vrt_path))

        # Determine the EXTENT
        output_bounds: Bounds = get_bounds_from_name(output_tile)
        min_x = output_bounds.point.x
        max_y = output_bounds.point.y
        min_y = max_y - output_bounds.size.height
        max_x = min_x + output_bounds.size.width

        # Create base COG from original file
        base_cog = os.path.join(output_dir, f"{output_tile}_c-LZW.tiff")
        custom_translate = get_custom_translate(
            compression="LZW",
            input_file=vrt_path,
            output_file=base_cog,
            extent_max=Point(max_x, max_y),
            extent_min=Point(min_x, min_y),
            driver="COG",
        )
        run_gdal(command=custom_translate)

        output_files.append(base_cog)

    return output_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", required=True)
    arguments = parser.parse_args()
    source = arguments.source

    compressions_input: List[Dict[str, str | int]] = [
        {"driver": "COG", "type": "LZW", "predictor": 2, "level": 0},
        {"driver": "COG", "type": "LZW", "predictor": 3, "level": 0},
        {"driver": "COG", "type": "ZSTD", "predictor": 0, "level": 9},
        {"driver": "COG", "type": "ZSTD", "predictor": 0, "level": 15},
        {"driver": "COG", "type": "ZSTD", "predictor": 0, "level": 22},
        {"driver": "COG", "type": "ZSTD", "predictor": 2, "level": 9},
        {"driver": "COG", "type": "ZSTD", "predictor": 2, "level": 12},
        {"driver": "COG", "type": "ZSTD", "predictor": 2, "level": 15},
        {"driver": "COG", "type": "ZSTD", "predictor": 3, "level": 9},
        {"driver": "COG", "type": "ZSTD", "predictor": 3, "level": 12},
        {"driver": "COG", "type": "ZSTD", "predictor": 3, "level": 15},
        {"driver": "COG", "type": "DEFLATE", "predictor": 0, "level": 0},
        {"driver": "COG", "type": "DEFLATE", "predictor": 2, "level": 0},
        {"driver": "COG", "type": "DEFLATE", "predictor": 3, "level": 0},
    ]
    compressions = [
        Compression(str(c["driver"]), str(c["type"]), int(c["predictor"]), int(c["level"])) for c in compressions_input
    ]

    # Create report CSV file
    report = open(os.path.join(source, "report.csv"), "w", encoding="UTF8")
    report_w = csv.writer(report)
    report_w.writerow(["file_name", "driver", "compression", "predictor", "level", "size (MB)", "duration (ms)"])

    source_files = [os.path.join(source, f) for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
    retiled_cogs = retile(source_files, 10000, source, "CF15_10000_0202")

    for cog in retiled_cogs:
        # Convert the base COG to GTiff to make the test more "real"
        # We never receive COG Tiffs
        base_compression = Compression("GTiff", "LZW", 0, 0)
        output_dir = os.path.dirname(cog)
        tile_name = os.path.basename(output_dir)
        compress_result = compress(base_compression, cog, tile_name, output_dir)
        base_gtiff = os.path.join(output_dir, str(compress_result[0]))
        report_w.writerow(compress_result)

        # Experiment various compressions
        for compression in compressions:
            report_w.writerow(
                compress(compression=compression, input_file=base_gtiff, tile_name=tile_name, output_dir=output_dir)
            )
        report.close()


if __name__ == "__main__":
    main()
