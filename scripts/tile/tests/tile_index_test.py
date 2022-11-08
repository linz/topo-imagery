from scripts.tile.tests.tile_index_data import MAP_SHEET_DATA
from scripts.tile.tile_index import Point, get_tile_name


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
