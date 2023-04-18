from scripts.gdal.gdalinfo import format_wkt, get_origin
from scripts.gdal.tests.gdalinfo import fake_gdal_info
from scripts.tile.tile_index import Point


def test_format_wkt() -> None:
    gdalinfo_wkt_output = '"NZGD2000 / New Zealand Transverse Mercator 2000",\n    BASEGEOGCRS["NZGD2000",\n        DAT'
    gdalinfo_wkt_formatted = format_wkt(gdalinfo_wkt_output)

    assert gdalinfo_wkt_formatted == "'NZGD2000 / New Zealand Transverse Mercator 2000', BASEGEOGCRS['NZGD2000', DAT"


def test_get_origin() -> None:
    gdalinfo = fake_gdal_info()
    gdalinfo["cornerCoordinates"] = {"upperLeft": [1, 2]}
    origin = Point(1, 2)
    origin_from_gdalinfo = get_origin(gdalinfo)
    assert origin == origin_from_gdalinfo
