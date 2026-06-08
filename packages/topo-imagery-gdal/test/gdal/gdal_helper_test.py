from pytest_subtests import SubTests

from topo_imagery_gdal.gdal.gdal_helper import is_geotiff
from topo_imagery_gdal.testing.gdalinfo import fake_gdal_info


def test_is_geotiff(subtests: SubTests) -> None:
    gdalinfo_geotiff = fake_gdal_info()
    gdalinfo_not_geotiff = fake_gdal_info()
    gdalinfo_geotiff["driverShortName"] = "GTiff"
    gdalinfo_not_geotiff["driverShortName"] = "GTiff"
    gdalinfo_geotiff["coordinateSystem"] = {"wkt": "PROJCRS['NZGD2000 / New Zealand Transverse Mercator 2000']"}

    with subtests.test():
        assert is_geotiff("file.tiff", gdalinfo_geotiff) is True

    with subtests.test():
        assert is_geotiff("file.tiff", gdalinfo_not_geotiff) is False
