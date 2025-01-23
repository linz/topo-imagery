from pytest_subtests import SubTests

from scripts.files.files_helper import convert_s3_paths, flatten_file_list, is_tiff
from scripts.gdal.gdal_helper import is_geotiff
from scripts.gdal.tests.gdalinfo import fake_gdal_info


def test_is_tiff(subtests: SubTests) -> None:
    file_a = "file.tiff"
    file_b = "file.tif"
    file_c = "file.TIFF"
    file_d = "file.jpg"

    with subtests.test():
        assert is_tiff(file_a) is True

    with subtests.test():
        assert is_tiff(file_b) is True

    with subtests.test():
        assert is_tiff(file_c) is True

    with subtests.test():
        assert is_tiff(file_d) is False


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


def test_flatten_file_list_flattens_nested_list(subtests: SubTests) -> None:
    nested_list = [["file1.tiff"], ["file2.json", "file3.geojson"]]
    expected_output = ["file1.tiff", "file2.json", "file3.geojson"]
    with subtests.test():
        assert flatten_file_list(nested_list) == expected_output


def test_flatten_file_list_handles_empty_lists(subtests: SubTests) -> None:
    with subtests.test():
        assert flatten_file_list([]) == []
    with subtests.test():
        assert flatten_file_list([[]]) == []
    with subtests.test():
        assert flatten_file_list([[], []]) == []


def test_convert_s3_paths_converts_paths_correctly(subtests: SubTests) -> None:
    flat_list = ["s3://bucket/file1.tiff", "s3://bucket/file2.json"]
    expected_output = ["/vsis3/bucket/file1.tiff", "/vsis3/bucket/file2.json"]
    with subtests.test():
        assert convert_s3_paths(flat_list) == expected_output


def test_convert_s3_paths_handles_empty_list(subtests: SubTests) -> None:
    with subtests.test():
        assert convert_s3_paths([]) == []
