from typing import NamedTuple, Union

from scripts.tile.util import charcodeat

SHEET_WIDTH = 24_000
""" Width of Topo 1:50k mapsheets (meters) """
SHEET_HEIGHT = 36_000
""" Height of Topo 1:50k mapsheets (meters) """
SHEET_ORIGIN_LEFT = 988_000
""" The NZTM x coordinate of the left edge of 1:50k mapsheets which would be at column position 00 """
SHEET_ORIGIN_TOP = 6_234_000
""" The NZTM y coordinate of the top edge of 1:50k mapsheets in row AS (the northernmost row) """
GRID_SIZE_MAX = 50_000
""" Base scale Topo 1:50k mapsheets (meters) """
CHAR_A = charcodeat("A", 0)
CHAR_S = charcodeat("S", 0)


class Point(NamedTuple):
    """Class that represents a point(x,y)"""

    x: Union[int, float]
    y: Union[int, float]


class Size(NamedTuple):
    width: Union[int, float]
    height: Union[int, float]


class Bounds(NamedTuple):
    point: Point
    size: Size


def get_bounds_from_name(tile_name: str) -> Bounds:
    """Get the origin coordinates and size of the tile from its name.

    Args:
        tile_name: the tile name as `sheetCode_gridSize_tileId`

    Returns:
        a `Bounds` object
    """
    name_parts = tile_name.split("_")
    map_sheet = name_parts[0]
    # should be in [50_000, 10_000, 5_000, 2_000, 1_000, 500]
    grid_size = int(name_parts[1])

    x = int(name_parts[2][-2:])
    y = int(name_parts[2][:2])
    if grid_size == 500:
        x = int(name_parts[2][-3:])
        y = int(name_parts[2][:3])

    origin = get_mapsheet_offset(map_sheet)
    tile_offset = get_tile_offset(grid_size=grid_size, x=x, y=y)
    return Bounds(
        Point(x=origin.x + tile_offset.point.x, y=origin.y - tile_offset.point.y),
        Size(tile_offset.size.width, tile_offset.size.height),
    )


def get_mapsheet_offset(sheet_code: str) -> Point:
    """Convert a mapsheet code into the origin point for the mapsheet

    Args:
        sheet_code: topo 50 map sheet code eg "CG10"

    Returns:
        Point: The top left point of the mapsheet

    Example:
        >>> get_mapsheet_offset("CG10")
        Point(x=1228000, y=4866000)
    """

    # from a mapsheet of "CG10", Y offset is "CG", X offset is 10
    # Y:"CG" x:"10"
    x = int(sheet_code[-2:])  # x = 10

    ms = sheet_code[:2]  # 'CG'
    # position difference of "S" and "A" as mapsheets start at "AS"
    base_y_offset = CHAR_S - CHAR_A
    # "C" -> C:67 - A:65 = 2 * 26 (Mapsheet codes A-Z)
    first_letter_offset = (charcodeat(ms, 0) - CHAR_A) * 26
    # "G" -> G:71 - A:65 = 6
    second_letter_offset = charcodeat(ms, 1) - CHAR_A

    y = first_letter_offset + second_letter_offset - base_y_offset

    # There are three missing map sheets
    if ms > "CI":
        y -= 3
    elif ms > "BO":
        y -= 2
    elif ms > "BI":
        y -= 1

    return Point(x=SHEET_WIDTH * x + SHEET_ORIGIN_LEFT, y=SHEET_ORIGIN_TOP - SHEET_HEIGHT * y)


def get_tile_offset(grid_size: int, x: int, y: int) -> Bounds:
    """Get the tile offset from its coordinate and the grid size

    Args:
        grid_size: a size from in [50_000, 10_000, 5_000, 2_000, 1_000, 500]
        x: upper left cooridinate x
        y: upper left cooridinate y

    Returns:
        a `Bounds` object
    """
    scale = grid_size / GRID_SIZE_MAX
    offset_x = SHEET_WIDTH * scale
    offset_y = SHEET_HEIGHT * scale
    return Bounds(Point(x=(x - 1) * offset_x, y=(y - 1) * offset_y), Size(width=offset_x, height=offset_y))
