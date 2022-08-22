from scripts.stac.imagery_stac import ImageryItem


def test_imagery_stac_item(mocker) -> None:  # type: ignore

    path = "./test/BR34_5000_0302.tiff"
    geometry = [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    date = "2021-01-27 00:00:00Z"
    # create item
    mocker.patch(
        "scripts.stac.util.checksum.multihash_as_hex",
        return_value="1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4",
    )
    item = ImageryItem(path, date, geometry, bbox)
    item.create_core_item()
    # checks
    assert item.stac["id"] == "BR34_5000_0302"
    assert item.stac["properties"]["datetime"] == date
    assert item.stac["geometry"]["coordinates"] == [geometry]
    assert item.stac["bbox"] == bbox
    assert (
        item.stac["assets"]["image"]["file:checksum"] == "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    )
