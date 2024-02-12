from scripts.gdal.gdalinfo import get_origin
from scripts.gdal.tests.gdalinfo import fake_gdal_info
from scripts.tile.tile_index import Point


def test_get_origin() -> None:
    gdalinfo = fake_gdal_info()
    gdalinfo["cornerCoordinates"] = {"upperLeft": [1, 2]}
    origin = Point(1, 2)
    origin_from_gdalinfo = get_origin(gdalinfo)
    assert origin == origin_from_gdalinfo
