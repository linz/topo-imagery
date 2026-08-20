import pytest
from pytest_subtests import SubTests
from tile_index_data import CHATHAM_SHEET_DATA, MAP_SHEET_DATA
from topo_imagery_common.epsg import EpsgNumber
from topo_imagery_gdal.tile.tile_index import (
    Bounds,
    Point,
    Size,
    get_bounds_from_name,
    get_chatham_mapsheet_offset,
    get_mapsheet_offset,
    get_tile_offset,
)


def test_get_bounds_from_name() -> None:
    expected_bounds = Bounds(Point(x=1236640, y=4837560), Size(width=240, height=360))
    bounds = get_bounds_from_name("CG10_500_080037")
    assert expected_bounds == bounds


def test_get_bounds_from_50k_name() -> None:
    expected_bounds = Bounds(Point(x=1180000, y=4758000), Size(width=24_000, height=36_000))
    bounds = get_bounds_from_name("CK08")
    assert expected_bounds == bounds


def test_get_bounds_from_name_chatham() -> None:
    # Regression test for failing tile: mainland arithmetic previously produced
    # EXTENT=1144000.0,4772400.0,1146400.0,4776000.0 for this tile, not the
    # tile's real EPSG:3793 location, causing gdal_translate to fail with
    # "Failed to compute statistics, no valid pixels found in sampling".
    expected_bounds = Bounds(Point(x=3518000, y=5086000), Size(width=2400, height=3600))
    bounds = get_bounds_from_name("CI06_5000_0606", target_epsg=EpsgNumber.CITM_2000)
    assert expected_bounds == bounds


def test_get_bounds_from_name_defaults_to_mainland() -> None:
    assert get_bounds_from_name("CK08") == get_bounds_from_name("CK08", target_epsg=EpsgNumber.NZTM_2000)


def test_get_bounds_from_50k_name_chatham() -> None:
    expected_bounds = Bounds(Point(x=3506000, y=5104000), Size(width=24_000, height=36_000))
    bounds = get_bounds_from_name("CI06", target_epsg=EpsgNumber.CITM_2000)
    assert expected_bounds == bounds


def test_get_bounds_from_name_chatham_without_target_epsg_fails_loudly() -> None:
    # Omitting target_epsg for a Chatham tile name must not silently default to mainland
    # arithmetic (see the regression test above) - it should fail loudly instead.
    with pytest.raises(ValueError, match="Unknown mainland map sheet"):
        get_bounds_from_name("CI06_5000_0606")


def test_get_bounds_from_name_unsupported_epsg() -> None:
    with pytest.raises(ValueError, match="Unsupported target EPSG"):
        get_bounds_from_name("CI06_5000_0606", target_epsg=2194)


@pytest.mark.dependency()
def test_get_tile_offset() -> None:
    expected_bounds = Bounds(Point(x=8640, y=28440), Size(width=240, height=360))
    bounds = get_tile_offset(grid_size=500, x=37, y=80)
    assert expected_bounds == bounds


@pytest.mark.dependency(depends=["test_get_tile_offset"])
def test_get_mapsheet_offset(subtests: SubTests) -> None:
    # Point(x=SHEET_WIDTH * x + SHEET_ORIGIN_LEFT, y=SHEET_ORIGIN_TOP - SHEET_HEIGHT * y)
    for sheet_data in MAP_SHEET_DATA:
        sheet_code = sheet_data["code"]
        map_sheet_offset = get_mapsheet_offset(sheet_code)
        origin = Point(x=sheet_data["origin"]["x"], y=sheet_data["origin"]["y"])
        with subtests.test(msg=sheet_code):
            assert map_sheet_offset == origin


def test_get_chatham_mapsheet_offset(subtests: SubTests) -> None:
    for sheet_data in CHATHAM_SHEET_DATA:
        sheet_code = sheet_data["code"]
        chatham_sheet_offset = get_chatham_mapsheet_offset(sheet_code)
        origin = Point(x=sheet_data["origin"]["x"], y=sheet_data["origin"]["y"])
        with subtests.test(msg=sheet_code):
            assert chatham_sheet_offset == origin


def test_get_chatham_mapsheet_offset_unknown_sheet() -> None:
    with pytest.raises(ValueError, match="Unknown Chatham Islands map sheet"):
        get_chatham_mapsheet_offset("CI99")


def test_get_mapsheet_offset_unknown_sheet(subtests: SubTests) -> None:
    # "CI" is reserved for the Chatham Islands and out of range for the mainland grid; "AS23" is a
    # real row with a gap that skips column 23 (see SHEET_RANGES["AS"] = [(21, 22), (24, 24)]).
    for sheet_code in ["CI05", "CI22", "AS23"]:
        with subtests.test(msg=sheet_code):
            with pytest.raises(ValueError, match="Unknown mainland map sheet"):
                get_mapsheet_offset(sheet_code)
