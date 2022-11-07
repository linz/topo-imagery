from enum import Enum
from typing import Any, Dict, Iterator, NamedTuple, Optional, Union

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


class TileIndexScale(Enum):
    scale_10000 = 10000
    scale_5000 = 5000
    scale_2000 = 2000
    scale_1000 = 1000
    scale_500 = 500


class XY(NamedTuple):
    x: Union[int, float]
    y: Union[int, float]


class TileBase:
    """
    Parent class for Tile and Sheet to inherit from
    """

    schema: Dict[str, Union[str, Dict[str, str]]]
    # pylint: disable=too-many-arguments
    def __init__(self, min_x: int, min_y: int, max_x: int, max_y: int, sheet_code: str):
        self.min_x: int = min_x
        self.min_y: int = min_y
        self.max_x: int = max_x
        self.max_y: int = max_y
        self.sheet_code: str = sheet_code

    @property
    def name(self) -> str:
        """The name of each instance, implemented in child classes"""
        raise NotImplementedError

    @property
    def ul(self) -> XY:
        """Upper left corner"""
        return XY(self.min_x, self.max_y)

    @property
    def ur(self) -> XY:
        """Upper right corner"""
        return XY(self.max_x, self.max_y)

    @property
    def lr(self) -> XY:
        """Lower right corner"""
        return XY(self.max_x, self.min_y)

    @property
    def ll(self) -> XY:
        """Lower left corner"""
        return XY(self.min_x, self.min_y)

    @property
    def centroid(self) -> XY:
        """Centre of the tile"""
        return XY(x=self.min_x + (self.max_x - self.min_x) / 2, y=self.min_y + (self.max_y - self.min_y) / 2)

    def contains(self, point: XY) -> bool:
        """Returns True if the supplied point is located within this tile, else false"""
        if self.min_x <= point.x < self.max_x and self.min_y < point.y <= self.max_y:
            return True
        return False

    def feature(self) -> Dict[str, Dict[str, Any]]:
        """The instance formatted as a fiona-format feature record"""
        return {"geometry": self.feature_geometry(), "properties": self.feature_properties()}

    def feature_properties(self) -> Dict[str, Any]:
        """The properties portion of the feature record, implemented in child classes"""
        raise NotImplementedError

    def feature_geometry(self) -> Dict[str, Any]:
        """The geometry portion of the feature record"""
        return {"type": "Polygon", "coordinates": [[self.ul, self.ur, self.lr, self.ll, self.ul]]}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


class Tile(TileBase):
    """
    Class representing a tile within a tile index at a given scale,
    being one of the members of TileIndexScale.
    """

    schema = {"geometry": "Polygon", "properties": {"TILENAME": "str", "MAPSHEET": "str", "SCALE": "int", "TILE": "str"}}
    # pylint: disable=too-many-arguments
    def __init__(self, min_x: int, min_y: int, max_x: int, max_y: int, sheet_code: str, scale: TileIndexScale, id_: str):
        self.scale: TileIndexScale = scale
        self.id: str = id_
        super().__init__(min_x, min_y, max_x, max_y, sheet_code)

    @property
    def name(self) -> str:
        return f"{self.sheet_code}_{self.scale.value}_{self.id}"

    def feature_properties(self) -> Dict[str, Union[str, int]]:
        return {"index_tile_id": self.name, "sheet_code_id": self.sheet_code, "scale": self.scale.value, "tile": self.id}


class Sheet(TileBase):
    """
    Class representing a sheet within a 1:50k tile index.
    """

    schema = {"geometry": "Polygon", "properties": {"sheet_code_id": "str"}}

    def __init__(self, min_x: int, max_y: int, sheet_code: str):
        max_x = min_x + SHEET_WIDTH
        min_y = max_y - SHEET_HEIGHT
        super().__init__(min_x, min_y, max_x, max_y, sheet_code)

    @property
    def name(self) -> str:
        return self.sheet_code

    def feature_properties(self) -> Dict[str, str]:
        return {"sheet_code_id": self.sheet_code}


def _build_sheets() -> Dict[str, Sheet]:
    sheets = {}
    for y_offset, (letters, range_pairs) in enumerate(SHEET_RANGES.items()):
        max_y = SHEET_ORIGIN_TOP - (y_offset * SHEET_HEIGHT)
        for (start, end) in range_pairs:
            for x_offset in range(start, end + 1):
                min_x = SHEET_ORIGIN_LEFT + (x_offset * SHEET_WIDTH)
                sheet_code = f"{letters}{x_offset:02d}"
                sheets[sheet_code] = Sheet(min_x, max_y, sheet_code)
    return sheets


class TileIndex:
    """
    Class representing a tile index at a given scale, being one of the members
    of TileIndexScale.
    """

    sheets = _build_sheets()

    def __init__(self, scale: TileIndexScale):
        if not isinstance(scale, TileIndexScale):
            raise ValueError("scale must be one of TileIndexScale Enum")
        self.scale: TileIndexScale = scale
        self.tiles: Dict[str, Tile] = {}

        # How many tiles there are across a 1:50k Sheet at this scale
        self.divisions: int = 50_000 // scale.value
        # The width of a tile at this scale in metres
        self.tile_width: int = SHEET_WIDTH // self.divisions
        # The height of a tile at this scale in metres
        self.tile_height: int = SHEET_HEIGHT // self.divisions
        # The number of digits long each component of the tile id is at this scale.
        if scale == TileIndexScale.scale_500:
            self.id_length = 3
        else:
            self.id_length = 2

    def get_sheet(self, sheet_code: str) -> Sheet:
        """
        Returns a Sheet instance of the supplied sheet_code.

        Will raise a ValueError if sheet_code is not one of the keys of TileIndex.sheets.
        """
        try:
            return self.sheets[sheet_code]
        except KeyError as ke:
            raise ValueError(f"{sheet_code} is not a valid sheet_code, must be a value contained in TileIndex.sheets") from ke

    def get_sheet_from_point(self, point: XY) -> Optional[Sheet]:
        """
        Returns the sheet which contains the supplied point.
        """
        if not SHEET_MIN_X <= point.x <= SHEET_MAX_X:
            raise ValueError(f"point.x must be between {SHEET_MIN_X} and {SHEET_MAX_X}, was {point.x}")
        if not SHEET_MIN_Y <= point.y <= SHEET_MAX_Y:
            raise ValueError(f"point.y must be between {SHEET_MIN_Y} and {SHEET_MAX_Y}, was {point.y}")
        x_offset = int((point.x - SHEET_ORIGIN_LEFT) // SHEET_WIDTH)
        y_offset = int((SHEET_ORIGIN_TOP - point.y) // SHEET_HEIGHT)
        letters = list(SHEET_RANGES.keys())[y_offset]
        sheet_code = f"{letters}{x_offset:02d}"
        sheet = self.sheets[sheet_code]

        if sheet.contains(point):
            return sheet
        return None

    def get_tile(self, sheet_code: str, x_index: int, y_index: int) -> Tile:
        """
        Returns a Tile instance at an x and y location within a sheet.

        Will raise a ValueError if sheet_code is not one of the keys of TileIndex.sheets,
        or if either x_index or y_index are not integers greater than 0 and less than
        self.divisions, the number tiles across each sheet at this scale.
        """
        if not isinstance(x_index, int) or not 0 < x_index <= self.divisions:
            raise ValueError(f"x must be an int greater than 0 and less than {self.divisions}, was {x_index}")
        if not isinstance(y_index, int) or not 0 < y_index <= self.divisions:
            raise ValueError(f"y must be an int greater than 0 and less than {self.divisions}, was {y_index}")
        sheet = self.get_sheet(sheet_code)
        tile_id = f"{y_index:0{self.id_length}d}{x_index:0{self.id_length}d}"
        tile_name = f"{sheet.name}_{self.scale}_{tile_id}"
        if tile_name in self.tiles:
            return self.tiles[tile_name]

        tile = Tile(
            min_x=int(sheet.ul.x + (x_index - 1) * self.tile_width),
            min_y=int(sheet.ul.y - y_index * self.tile_height),
            max_x=int(sheet.ul.x + x_index * self.tile_width),
            max_y=int(sheet.ul.y - (y_index - 1) * self.tile_height),
            sheet_code=sheet.name,
            scale=self.scale,
            id_=tile_id,
        )
        self.tiles[tile.name] = tile
        return tile

    def get_tile_from_point(self, point: XY) -> Optional[Tile]:
        """
        Returns the tile which contains the supplied point.
        Will return None if the point is not contained within any tiles.
        """
        if sheet := self.get_sheet_from_point(point):
            tile_x = int((point.x - sheet.ul.x) // self.tile_width + 1)
            tile_y = int((sheet.ul.y - point.y) // self.tile_height + 1)
            return self.get_tile(sheet.name, tile_x, tile_y)

        return None

    def iter_tiles_in_sheet(self, sheet_code: str) -> Iterator[Tile]:
        """
        Provides an iterator through all tiles in a sheet. Will raise a ValueError if sheet_code
        is not a valid sheet_code contained in TileIndex.sheets.
        """
        if sheet_code not in self.sheets:
            raise ValueError(f"{sheet_code} is not a valid sheet_code, must be a value contained in TileIndex.sheets")
        for x in range(1, self.divisions + 1):
            for y in range(1, self.divisions + 1):
                yield self.get_tile(sheet_code, x, y)

    def iter_all_tiles(self) -> Iterator[Tile]:
        """Provides an iterator through all tiles in all sheets."""

        for sheet_code in self.sheets:
            for tile in self.iter_tiles_in_sheet(sheet_code):
                yield tile


def id_to_xy(id_: str) -> XY:
    """
    Converts a tile id string of the format 012034 to an XY NamedTuple of the form XY(x=34, y=12).
    Will raise a ValueError if id_ is not a string of an even length of characters,
    all of which are digits.
    """
    error_msg = "id_ must be a str of an even length of characters, all of which are digits"
    if not isinstance(id_, str):
        raise ValueError(error_msg)
    length = len(id_)
    if length % 2 != 0 or not id_.isdigit():
        raise ValueError(error_msg)
    x = int(id_[length // 2 :])
    y = int(id_[0 : length // 2])
    return XY(x=x, y=y)


def get_origin_from_gdalinfo(gdalinfo: Dict[Any, Any]) -> XY:
    return XY(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])


def check_alignement(origin: XY, scale: int) -> str | None:
    """Validate the tiff file against tile indexes

    Args:
        path (str): the tiff path
        scale (Optional[TileIndexScale]): the scale for the tile index. Try to get it from the tiff file name if not provided.

    Returns:
        str: the filename is tiff is valid against the tile index. None if not valid.
    """
    # Get the scale from the original file name
    tile_index_scale = TileIndexScale(scale)
    index = TileIndex(tile_index_scale)
    tile = index.get_tile_from_point(origin)
    if not tile.name:
        return None
    return str(tile.name)
