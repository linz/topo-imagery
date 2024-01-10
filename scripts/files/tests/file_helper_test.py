from scripts.files.files_helper import is_geotiff, is_tiff
from scripts.gdal.tests.gdalinfo import fake_gdal_info


def test_is_tiff() -> None:
    file_a = "file.tiff"
    file_b = "file.tif"
    file_c = "file.TIFF"
    file_d = "file.jpg"

    assert is_tiff(file_a) is True
    assert is_tiff(file_b) is True
    assert is_tiff(file_c) is True
    assert is_tiff(file_d) is False


def test_is_geotiff() -> None:
    gdalinfo_geotiff = fake_gdal_info()
    gdalinfo_not_geotiff = fake_gdal_info()
    gdalinfo_geotiff["driverShortName"] = "GTiff"
    gdalinfo_not_geotiff["driverShortName"] = "GTiff"
    gdalinfo_geotiff["coordinateSystem"] = {"wkt": "PROJCRS['NZGD2000 / New Zealand Transverse Mercator 2000']"}

    assert is_geotiff("file.tiff", gdalinfo_geotiff) is True
    assert is_geotiff("file.tiff", gdalinfo_not_geotiff) is False
