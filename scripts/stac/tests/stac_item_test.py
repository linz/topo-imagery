from scripts.files.files_helper import get_file_name_from_path, strip_extension
from scripts.stac.item import ImageryItem


def test_imagery_stac_item() -> None:
    path = "./scripts/stac/tests/data/RGB_BD33_0709.tiff"
    item = ImageryItem(strip_extension(get_file_name_from_path(path)))
    item.create_stac_item(path, "2021-01-27 00:00:00Z")
    assert item.id == "RGB_BD33_0709"
    assert item.stac["id"] == "RGB_BD33_0709"
    assert item.stac["geometry"]["coordinates"] == [[[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]]
    assert item.stac["bbox"] == [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    assert item.stac["assets"]["image"]["checksum:multihash"] == "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
