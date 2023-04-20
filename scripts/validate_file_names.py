import argparse
import json
from typing import Dict, List

from linz_logger import get_log

from scripts.gdal.gdalinfo import gdal_info, get_origin
from scripts.tile.tile_index import get_tile_name


class DuplicateFileException(Exception):
    pass


def _parse_file_list(file_list_path: str) -> List[str]:
    """if there is more that one 'sublist' due to aws-list grouping, they must be merged.

    Args:
        file_list_path (str): local path to json file listing paths

    Returns:
        List[str]: combined list of source files
    """
    with open(file_list_path, "r", encoding="utf-8") as data:
        file_list: List[List[str]] = json.loads(data.read())

    if len(file_list) > 1:
        return [element for nestedlist in file_list for element in nestedlist]

    return file_list[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-list", dest="file_list", required=True, help="Local path to file_list json")
    parser.add_argument("--scale", dest="scale", required=True, help="Tile grid scale to align output tile to")

    arguments = parser.parse_args()
    file_list = _parse_file_list(arguments.file_list)

    files: Dict[str, str] = {}
    duplicates: List[str] = []

    for file in file_list:
        get_log().info("Checking File", source=file)

        original_gdalinfo = gdal_info(file, False)
        origin = get_origin(original_gdalinfo)
        tile_name = get_tile_name(origin, int(arguments.scale))
        standardized_file_name = f"{tile_name}.tiff"

        if standardized_file_name in files:
            duplicates.append(
                f"File '{file}' with target '{standardized_file_name}' duplicates '{files[standardized_file_name]}'"
            )
            continue

        files[standardized_file_name] = file

    if len(duplicates) > 0:
        raise DuplicateFileException(f"Duplicates Found:\n {duplicates}")


if __name__ == "__main__":
    main()
