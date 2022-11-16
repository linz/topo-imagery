from pytest import CaptureFixture, raises

from scripts.tile.tests.tile_index_data import MAP_SHEET_DATA
from scripts.tile.tile_index import Point, TileIndexException, get_tile_name, round_with_correction


def test_check_alignment_build_correct_sheet_code() -> None:
    for sheet in MAP_SHEET_DATA:
        origin = Point(sheet["origin"]["x"], sheet["origin"]["y"])
        sheet_code = sheet["code"]
        generated_name = get_tile_name(origin, 500)
        assert sheet_code in generated_name


def test_check_alignment_generate_correct_name() -> None:
    file_name = "CG10_500_080037.tiff"
    origin = Point(1236640, 4837560)
    tile_name = get_tile_name(origin, 500)
    assert tile_name + ".tiff" == file_name


def test_check_alignment_generate_correct_name_when_origin_drift() -> None:
    """This tiff should not be renammed 'BP27_1000_4816.tiff'"""
    file_name = "BP27_1000_4817.tiff"
    origin = Point(1643679.999967818148434, 5444159.999954843893647)
    tile_name = get_tile_name(origin, 1000)
    assert tile_name + ".tiff" == file_name


def test_check_alignment_generate_correct_name_when_origin_driftti(capsys: CaptureFixture[str]) -> None:
    origin_a = Point(1643679, 5444159.01535345)
    origin_b = Point(1643679.984567, 5444159)
    with raises(TileIndexException):
        get_tile_name(origin_a, 1000)
        sysout = capsys.readouterr()
        assert "origin is invalid" in sysout.out
    with raises(TileIndexException):
        get_tile_name(origin_b, 1000)
        sysout = capsys.readouterr()
        assert "origin is invalid" in sysout.out


def test_round_origin() -> None:
    assert round_with_correction(1643679.999967818148434) == 1643680
    assert round_with_correction(1643679.99) == 1643680
    assert round_with_correction(1643680.01) == 1643680
    assert round_with_correction(1643680.05) == 1643680.05
    assert round_with_correction(1643679.969) == 1643679.97
    assert round_with_correction(5444160.051) == 5444160.05
    assert round_with_correction(5444160.015) == 5444160
    assert round_with_correction(5444160.985) == 5444161
