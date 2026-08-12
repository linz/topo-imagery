from fake_gdalinfo import fake_gdalinfo
from pytest_subtests import SubTests
from topo_imagery_common.epsg import EpsgNumber
from topo_imagery_gdal.gdal.gdal_helper import get_srs_command, is_geotiff


def test_is_geotiff(subtests: SubTests) -> None:
    gdalinfo_geotiff = fake_gdalinfo()
    gdalinfo_not_geotiff = fake_gdalinfo()
    gdalinfo_geotiff["driverShortName"] = "GTiff"
    gdalinfo_not_geotiff["driverShortName"] = "GTiff"
    gdalinfo_geotiff["coordinateSystem"] = {"wkt": "PROJCRS['NZGD2000 / New Zealand Transverse Mercator 2000']"}

    with subtests.test():
        assert is_geotiff("file.tiff", gdalinfo_geotiff) is True

    with subtests.test():
        assert is_geotiff("file.tiff", gdalinfo_not_geotiff) is False


def test_get_srs_command_uses_the_given_epsg(subtests: SubTests) -> None:
    with subtests.test("NZTM"):
        assert get_srs_command(EpsgNumber.NZTM_2000)[-1] == "EPSG:2193"

    with subtests.test("Chatham Islands"):
        assert get_srs_command(EpsgNumber.CITM_2000)[-1] == "EPSG:3793"
