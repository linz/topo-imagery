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


class TileIndexException(Exception):
    pass


class Point(NamedTuple):
    x: Union[int, float]
    y: Union[int, float]


def get_tile_name(origin: Point, grid_size: int) -> str:
    # pylint: disable-msg=too-many-locals
    if not grid_size in GRID_SIZES:
        raise TileIndexException(f"The scale has to be one of the following values: {GRID_SIZES}")

    origin_x = origin[0]
    origin_y = origin[1]
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

    offset_x = int((origin_x - SHEET_ORIGIN_LEFT) // SHEET_WIDTH)
    offset_y = int((SHEET_ORIGIN_TOP - origin_y) // SHEET_HEIGHT)
    max_y = SHEET_ORIGIN_TOP - (offset_y * SHEET_HEIGHT)
    min_x = SHEET_ORIGIN_LEFT + (offset_x * SHEET_WIDTH)
    tile_x = (origin_x - min_x) // tile_width + 1
    tile_y = (max_y - origin_y) // tile_height + 1

    letters = list(SHEET_RANGES)[offset_y]
    sheet_code = f"{letters}{offset_x:02d}"
    tile_id = f"{tile_y:0{nb_digits}d}{tile_x:0{nb_digits}d}"

    return f"{sheet_code}_{grid_size}_{tile_id}"
