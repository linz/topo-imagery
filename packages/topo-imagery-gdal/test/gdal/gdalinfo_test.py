from topo_imagery_gdal.gdal.gdalinfo import get_origin
from topo_imagery_gdal.testing.gdalinfo import fake_gdal_info
from topo_imagery_gdal.tile.tile_index import Point


def test_get_origin() -> None:
    gdalinfo = fake_gdal_info()
    gdalinfo["cornerCoordinates"] = {"upperLeft": [1, 2]}
    origin = Point(1, 2)
    origin_from_gdalinfo = get_origin(gdalinfo)
    assert origin == origin_from_gdalinfo
