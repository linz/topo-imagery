from fake_gdalinfo import fake_gdalinfo
from pytest_subtests import SubTests
from topo_imagery_common.epsg import EpsgNumber
from topo_imagery_gdal.gdal.gdal_helper import get_srs, is_geotiff


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


def test_get_srs_uses_the_given_epsg() -> None:
    nztm_srs = get_srs(EpsgNumber.NZTM_2000)
    citm_srs = get_srs(EpsgNumber.CITM_2000)
    assert nztm_srs != citm_srs
    assert b"Chatham Islands" in citm_srs
