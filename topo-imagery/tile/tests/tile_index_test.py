import pytest

from topo-imagery.tile.tests.tile_index_data import MAP_SHEET_DATA
from topo-imagery.tile.tile_index import Bounds, Point, Size, get_bounds_from_name, get_mapsheet_offset, get_tile_offset


def test_get_bounds_from_name() -> None:
    expected_bounds = Bounds(Point(x=1236640, y=4837560), Size(width=240, height=360))
    bounds = get_bounds_from_name("CG10_500_080037")
    assert expected_bounds == bounds


@pytest.mark.dependency()
def test_get_tile_offset() -> None:
    expected_bounds = Bounds(Point(x=8640, y=28440), Size(width=240, height=360))
    bounds = get_tile_offset(grid_size=500, x=37, y=80)
    assert expected_bounds == bounds


@pytest.mark.dependency(depends=["test_get_tile_offset"])
def test_get_mapsheet_offset() -> None:
    # Point(x=SHEET_WIDTH * x + SHEET_ORIGIN_LEFT, y=SHEET_ORIGIN_TOP - SHEET_HEIGHT * y)
    for sheet_data in MAP_SHEET_DATA:
        map_sheet_offset = get_mapsheet_offset(sheet_data["code"])
        origin = Point(x=sheet_data["origin"]["x"], y=sheet_data["origin"]["y"])
        assert map_sheet_offset == origin
