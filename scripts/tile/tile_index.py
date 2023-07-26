from logging import get_log
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
SHEET_MIN_X = SHEET_ORIGIN_LEFT + (4 * SHEET_WIDTH)
""" The minimum x coordinate of a valid sheet / tile """
SHEET_MAX_X = SHEET_ORIGIN_LEFT + (46 * SHEET_WIDTH)
""" The maximum x coordinate of a valid sheet / tile """
SHEET_MIN_Y = SHEET_ORIGIN_TOP - (41 * SHEET_HEIGHT)
""" The minimum y coordinate of a valid sheet / tile """
SHEET_MAX_Y = SHEET_ORIGIN_TOP
""" The maximum y coordinate of a valid sheet / tile """
SHEET_RANGES = {
    "AS": [(21, 22), (24, 24)],
    "AT": [(23, 26)],
    "AU": [(24, 29)],
    "AV": [(24, 30)],
    "AW": [(25, 32)],
    "AX": [(27, 33)],
    "AY": [(28, 35)],
    "AZ": [(28, 36)],
    "BA": [(29, 37)],
    "BB": [(30, 37)],
    "BC": [(30, 38), (40, 41)],
    "BD": [(31, 46)],
    "BE": [(31, 46)],
    "BF": [(30, 45)],
    "BG": [(29, 45)],
    "BH": [(28, 44)],
    "BJ": [(27, 43)],
    "BK": [(28, 40)],
    "BL": [(28, 40)],
    "BM": [(23, 25), (32, 39)],
    "BN": [(22, 29), (32, 38)],
    "BP": [(22, 37)],
    "BQ": [(21, 36)],
    "BR": [(19, 30), (32, 34)],
    "BS": [(19, 29)],
    "BT": [(18, 28)],
    "BU": [(16, 27)],
    "BV": [(15, 27)],
    "BW": [(14, 26)],
    "BX": [(12, 26)],
    "BY": [(10, 26)],
    "BZ": [(8, 23)],
    "CA": [(7, 22)],
    "CB": [(6, 20)],
    "CC": [(5, 20)],
    "CD": [(4, 19)],
    "CE": [(4, 18)],
    "CF": [(4, 17)],
    "CG": [(4, 16)],
    "CH": [(5, 14)],
    "CJ": [(7, 11)],
    "CK": [(7, 9)],
}
""" Ranges of valid sheet columns for each sheet row. 
Keys are the row names, and values are ranges between which there are valid rows. 
For example `"AS": [(21, 22), (24, 24)]` means the valid sheets in row AS are AS21, AS22, and AS24. 
See `sheet index diagram` at 
https://www.linz.govt.nz/products-services/maps/new-zealand-topographic-maps/topo50-map-chooser/topo50-sheet-index """

# FIXME: create an enum
GRID_SIZES = [10_000, 5_000, 2_000, 1_000, 500]
""" Allowed grid sized, these should exist in the LINZ Data service (meters) """
GRID_SIZE_MAX = 50_000
""" Base scale Topo 1:50k mapsheets (meters) """
ROUND_CORRECTION = 0.01
""" Correction set to `1` centimer """


class TileIndexException(Exception):
    pass
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

def round_with_correction(value: Union[int, float]) -> int | float:
    """Round a value to the next or previous unit ROUND_CORRECTION.
    Python round() can be 'inaccurate', note that:
        >>> round(0.015)
        0.01
        >>> round(0.985)
        0.99
    Args:
        value: the value to round with correction.
    Returns:
        the rounded and (maybe) corrected value.
    Examples:
        >>> round_with_correction(1643679.969)
        1643679.97
        >>> round_with_correction(5444160.015)
        5444160
    """
    if isinstance(value, int):
        return value
    # Round to centimeter precision
    correction = rounded_value = round(value, 2)
    # The rounded value is not an integer
    if not rounded_value.is_integer():
        # Try to get an integer by adding the `ROUND_CORRECTION`
        if (rounded_value + ROUND_CORRECTION).is_integer():
            correction = rounded_value + ROUND_CORRECTION
        # Try to get an integer by substracting the `ROUND_CORRECTION`
        elif (rounded_value - ROUND_CORRECTION).is_integer():
            correction = rounded_value - ROUND_CORRECTION

    if correction.is_integer():
        return int(correction)
    
    return correction

def get_tile_name(origin: Point, grid_size: int) -> str:
    """Get the tile name from an origin point and the grid size (or scale).

    Args:
        origin: The origin point of the tile to get the name for.
        grid_size: The size of the grid (or scale).

    Raises:
        TileIndexException: If the input data don't allow to get the tile.

    Returns:
        str: The generated tile name ('sheetCode_gridSize_tileId').
        Point: The top left point of the mapsheet
    Example:
        >>> get_tile_name(Point(1236640, 4837560), 500)
        "CG10_500_080037.tiff"
        >>> get_mapsheet_offset("CG10")
        Point(x=1228000, y=4866000)
    """
    # pylint: disable-msg=too-many-locals
    if not grid_size in GRID_SIZES:
        raise TileIndexException(f"The scale has to be one of the following values: {GRID_SIZES}")

    origin_x = round_with_correction(origin[0])
    origin_y = round_with_correction(origin[1])

    # If x or y is not a round number after being corrected, the origin is not valid
    if not isinstance(origin_x, int) or not isinstance(origin_y, int):
        raise TileIndexException(f"The origin is invalid x = {origin_x}, y = {origin_y}")

    scale = GRID_SIZE_MAX // grid_size
    tile_width = SHEET_WIDTH // scale
    tile_height = SHEET_HEIGHT // scale
    nb_digits = 2
    if grid_size == 500:
        nb_digits = 3  # 1:500 X/Y is 3 digits not 2

    if not SHEET_MIN_X <= origin_x <= SHEET_MAX_X:
        raise TileIndexException(f"x must be between {SHEET_MIN_X} and {SHEET_MAX_X}, was {origin_x}")
    if not SHEET_MIN_Y <= origin_y <= SHEET_MAX_Y:
        raise TileIndexException(f"y must be between {SHEET_MIN_Y} and {SHEET_MAX_Y}, was {origin_y}")
    # Do some maths
    offset_x = int((origin_x - SHEET_ORIGIN_LEFT) // SHEET_WIDTH)
    offset_y = int((SHEET_ORIGIN_TOP - origin_y) // SHEET_HEIGHT)
    max_y = SHEET_ORIGIN_TOP - (offset_y * SHEET_HEIGHT)
    min_x = SHEET_ORIGIN_LEFT + (offset_x * SHEET_WIDTH)
    tile_x = int((origin_x - min_x) // tile_width + 1)
    tile_y = int((max_y - origin_y) // tile_height + 1)
    # Build name
    letters = list(SHEET_RANGES)[offset_y]
    sheet_code = f"{letters}{offset_x:02d}"
    tile_id = f"{tile_y:0{nb_digits}d}{tile_x:0{nb_digits}d}"

    return f"{sheet_code}_{grid_size}_{tile_id}"


def get_bounds_from_name(tile_name: str) -> Bounds:
    """Get the origin coordinates and size of the tile from its name.

    Args:
        tile_name: the tile name as `sheetCode_gridSize_tileId`

    Returns:
        a `Bounds` object
    """
    name_parts = tile_name.split("_")
    map_sheet = name_parts[0]
    # should be in [10_000, 5_000, 2_000, 1_000, 500]
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
        grid_size: a size from in [10_000, 5_000, 2_000, 1_000, 500]
        x: upper left cooridinate x
        y: upper left cooridinate y

    Returns:
        a `Bounds` object
    """
    scale = grid_size / GRID_SIZE_MAX
    offset_x = SHEET_WIDTH * scale
    offset_y = SHEET_HEIGHT * scale
    return Bounds(Point(x=(x - 1) * offset_x, y=(y - 1) * offset_y), Size(width=offset_x, height=offset_y))
