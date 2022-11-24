from typing import NamedTuple, Union

SHEET_WIDTH = 24_000  # The width of a 1:50k sheet in metres
SHEET_HEIGHT = 36_000  # The height of a 1:50k sheet in metres
SHEET_ORIGIN_LEFT = 988_000  # The NZTM x coordinate of the left edge of 1:50k sheet which would be at column position 00
SHEET_ORIGIN_TOP = 6_234_000  # The NZTM y coordinate of the top edge of sheets in row AS (the northernmost row)
SHEET_MIN_X = SHEET_ORIGIN_LEFT + (4 * SHEET_WIDTH)  # The minimum x coordinate of a valid sheet / tile
SHEET_MAX_X = SHEET_ORIGIN_LEFT + (46 * SHEET_WIDTH)  # The maximum x coordinate of a valid sheet / tile
SHEET_MIN_Y = SHEET_ORIGIN_TOP - (41 * SHEET_HEIGHT)  # The minimum y coordinate of a valid sheet / tile
SHEET_MAX_Y = SHEET_ORIGIN_TOP  # The maximum y coordinate of a valid sheet / tile
# Ranges of valid sheet columns for each sheet row. Keys are the row names, and values are ranges
# between which there are valid rows. For example `"AS": [(21, 22), (24, 24)]` means the valid
# sheets in row AS are AS21, AS22, and AS24.
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
GRID_SIZES = [10_000, 5_000, 2_000, 1_000, 500]
GRID_SIZE_MAX = 50_000
# Correction is set to 1 centimeter
ROUND_CORRECTION = 0.01


class TileIndexException(Exception):
    pass


class Point(NamedTuple):
    """Class that represents a point(x,y)"""

    x: Union[int, float]
    y: Union[int, float]


def round_with_correction(value: Union[int, float]) -> int | float:
    """Round a value to the next or previous unit ROUND_CORRECTION.
    Python round() can be 'inaccurate', note that:
        round(0.015) == 0.01
        round(0.985) == 0.99

    Args:
        value (Union[int, float]): the value to round with correction.

    Returns:
        int | float: the rounded and (maybe) corrected value.
    """
    if isinstance(value, int):
        return value

    # Round to centimeter precision
    correction = rounded_value = round(value, 2)

    if not rounded_value.is_integer():
        if (rounded_value + ROUND_CORRECTION).is_integer():
            correction = rounded_value + ROUND_CORRECTION
        elif (rounded_value - ROUND_CORRECTION).is_integer():
            correction = rounded_value - ROUND_CORRECTION

    if correction.is_integer():
        return int(correction)

    return correction


def get_tile_name(origin: Point, grid_size: int) -> str:
    """Get the tile name from an origin point and the grid size (or scale).

    Args:
        origin (Point): The origin point of the tile to get the name for.
        grid_size (int): The size of the grid (or scale).

    Raises:
        TileIndexException: If the input data don't allow to get the tile.

    Returns:
        str: The generated tile name ('sheetCode_gridSize_tileId').
    """
    # pylint: disable-msg=too-many-locals
    if not grid_size in GRID_SIZES:
        raise TileIndexException(f"The scale has to be one of the following values: {GRID_SIZES}")

    origin_x = round_with_correction(origin[0])
    origin_y = round_with_correction(origin[1])

    # If x or y is not a round number, the origin is not valid
    if not isinstance(origin_x, int) or not isinstance(origin_y, int):
        raise TileIndexException(f"The origin is invalid x = {origin_x}, y = {origin_y}")

    scale = GRID_SIZE_MAX // grid_size
    tile_width = SHEET_WIDTH // scale
    tile_height = SHEET_HEIGHT // scale
    nb_digits = 2
    if grid_size == 500:
        nb_digits = 3

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
