from scripts.files.files_helper import get_file_name_from_path, strip_extension
from scripts.stac.imagery_stac import create_imagery_stac_item


def test_imagery_stac_item(mocker) -> None:  # type: ignore
    # mock functions that interact with files
    geometry = [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    checksum = "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    mocker.patch("scripts.stac.util.checksum.multihash_as_hex", return_value=checksum)
    mocker.patch("scripts.stac.util.geotiff.get_extents", return_value=(geometry, bbox))

    path = "./test/BR34_5000_0302.tiff"
    id_ = strip_extension(get_file_name_from_path(path))
    start_datetime = "2021-01-27 00:00:00Z"
    end_datetime = "2021-01-27 00:00:00Z"

    stac = create_imagery_stac_item(id_, path, start_datetime, end_datetime)
    # checks
    assert stac["id"] == id_
    assert stac["properties"]["start_datetime"] == start_datetime
    assert stac["properties"]["end_datetime"] == end_datetime
    assert stac["properties"]["datetime"] is None
    assert stac["geometry"]["coordinates"] == [geometry]
    assert stac["bbox"] == bbox
    assert stac["assets"]["image"]["file:checksum"] == checksum
