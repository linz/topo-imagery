from scripts.tile.tests.tile_index_data import MAP_SHEET_DATA
from scripts.tile.tile_index import XY, check_alignement


def test_check_alignment_build_correct_sheet_code() -> None:
    for sheet in MAP_SHEET_DATA:
        origin = XY(sheet["origin"]["x"], sheet["origin"]["y"])
        sheet_code = sheet["code"]
        generated_name = check_alignement(origin, scale=500)
        assert sheet_code in generated_name


def test_check_alignment_generate_correct_name() -> None:
    file_name = "CG10_500_080037.tiff"
    origin = XY(1236640, 4837560)
    generated_name = check_alignement(origin, scale=500)
    assert generated_name + ".tiff" == file_name
