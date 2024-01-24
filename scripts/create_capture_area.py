import argparse
import json
import os
import tempfile
from functools import partial
from multiprocessing import Pool

import shapely.geometry
from linz_logger import get_log

from scripts.files.files_helper import SUFFIX_FOOTPRINT, ContentType, get_file_name_from_path, is_tiff
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import run_gdal
from scripts.logging.time_helper import time_in_ms
from scripts.stac.imagery.capture_aera import generate_capture_area
from scripts.stac.imagery.collection import CAPTURE_AREA_FILE_NAME


def create_footprint(source_tiff: str, tmp_path: str, target: str) -> str | None:
    if not is_tiff(source_tiff):
        get_log().debug("create_footprint_skip_not_tiff", file=source_tiff)
        return None

    basename = get_file_name_from_path(source_tiff)
    target_footprint = os.path.join(target, f"{basename}{SUFFIX_FOOTPRINT}")
    # Verify the footprint has not been already generated
    if exists(target_footprint):
        get_log().info("footprint_already_exists", path=target_footprint)
        return None
    local_tiff = os.path.join(tmp_path, f"{basename}.tiff")
    # Download source tiff
    write(local_tiff, read(source_tiff))

    # Generate footprint
    run_gdal(
                ["gdal_footprint", "-t_srs", "EPSG:4326"],
                local_tiff,
                target_footprint,
            )
    
    return target_footprint


def main() -> None:
    start_time = time_in_ms()
    get_log().info("create_footprints_start")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file", dest="from_file", required=True, help="The path to a json file containing the input tiffs"
    )
    parser.add_argument("--target", dest="target", required=True, help="The path to save the capture-area.")
    arguments = parser.parse_args()
    from_file = arguments.from_file
    source = json.loads(read(from_file))

    concurrency = 25
    footprint_list = []

    with tempfile.TemporaryDirectory() as tmp_path:
        for tiff_list in source:
            with Pool(concurrency) as p:
                footprint_list_current = p.map(
                    partial(
                        create_footprint,
                        tmp_path=tmp_path,
                        target=tmp_path,
                    ),
                    tiff_list,
                )
                p.close()
                p.join()
                footprint_list.extend(footprint_list_current)

        # Load polygons from local footprint files
        polygons = []
        for footprint_file in footprint_list:
            f = open(footprint_file)
            content = json.load(f)
            polygons.append(shapely.geometry.shape(content["features"][0]["geometry"]))
            f.close()

        capture_area_content = generate_capture_area(polygons)
        capture_area_target = os.path.join(arguments.target, CAPTURE_AREA_FILE_NAME)
        write(
                capture_area_target,
                json.dumps(capture_area_content).encode("utf-8"),
                content_type=ContentType.GEOJSON.value,
            )
    
    get_log().info("create_capture_area_end", duration=time_in_ms() - start_time)


if __name__ == "__main__":
    main()
