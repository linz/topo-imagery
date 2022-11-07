from scripts.tile.tests.sheets_data import MAP_SHEET_DATA
from scripts.tile.tile_index import XY, check_alignement


def test_check_alignment_build_correct_sheet_code() -> None:
    for sheet in MAP_SHEET_DATA:
        origin = XY(sheet["origin"]["x"], sheet["origin"]["y"])
        sheet_code = sheet["code"]
        generated_name = check_alignement(origin, scale=500)
        assert sheet_code in generated_name
