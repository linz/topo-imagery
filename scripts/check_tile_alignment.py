import argparse
import sys
from typing import Any, Dict, Optional

from linz_logger import get_log

from scripts.cli.cli_helper import format_source
from scripts.files.files_helper import is_tiff
from scripts.tile.tile_index import XY, TileIndex, TileIndexScale


def validate(gdalinfo: Dict[Any, Any], scale: Optional[TileIndexScale]) -> str | None:
    """Validate the tiff file against tile indexes

    Args:
        path (str): the tiff path
        scale (Optional[TileIndexScale]): the scale for the tile index. Try to get it from the tiff file name if not provided.

    Returns:
        str: the filename is tiff is valid against the tile index. None if not valid.
    """

    # Get the scale from file name if not provided
    if scale is None:
        print("not yet implemented")
    else:
        # Get the scale from the original file name
        index = TileIndex(scale)
        tile = index.get_tile_from_point(
            XY(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])
        )
        return tile.name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument("--scale", dest="scale", help="Tile index scale", required=False)

    arguments = parser.parse_args()

    source = format_source(arguments.source)

    scale = arguments.scale

    files_in_error = []

    for file in source:
        if is_tiff(file):
            # gdalinfo the file
            valid_name = validate(file, TileIndexScale(int(scale)))
            if valid_name is not None:
                if valid_name in file:
                    get_log().info("success")
                else:
                    files_in_error.append(file)
        else:
            get_log().info("tile_index_validate_file_not_tiff_skipped", file=file)

    if len(files_in_error) > 0:
        get_log().error("file not correctly named", errors=files_in_error)
        sys.exit(1)


if __name__ == "__main__":
    main()
