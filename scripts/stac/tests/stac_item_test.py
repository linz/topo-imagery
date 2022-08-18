from scripts.files.files_helper import get_file_name_from_path, strip_extension
from scripts.stac import imagery_stac


def test_imagery_stac_item() -> None:
    # inputs
    path = "./test/RGB_BD33_0709.tiff"
    id_ = strip_extension(get_file_name_from_path(path))
    geometry = [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    checksum = "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    date = "2021-01-27 00:00:00Z"
    # create item
    stac = imagery_stac.create_item(id_, path, date, geometry, bbox, checksum)
    # checks
    assert stac["id"] == "RGB_BD33_0709"
    assert stac["properties"]["datetime"] == date
    assert stac["geometry"]["coordinates"] == [geometry]
    assert stac["bbox"] == bbox
    assert stac["assets"]["image"]["file:checksum"] == checksum
