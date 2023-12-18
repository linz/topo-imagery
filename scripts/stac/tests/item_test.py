from datetime import datetime

from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionTitleMetadata


def test_imagery_stac_item(mocker) -> None:  # type: ignore
    # mock functions that interact with files
    geometry = {
        "type": "Polygon",
        "coordinates": [[[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    checksum = "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    mocker.patch("scripts.stac.util.checksum.multihash_as_hex", return_value=checksum)

    path = "./test/BR34_5000_0302.tiff"
    id_ = get_file_name_from_path(path)
    start_datetime = "2021-01-27 00:00:00Z"
    end_datetime = "2021-01-27 00:00:00Z"

    item = ImageryItem(id_, path)
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)
    # checks
    assert item.stac["id"] == id_
    assert item.stac["properties"]["start_datetime"] == start_datetime
    assert item.stac["properties"]["end_datetime"] == end_datetime
    assert item.stac["properties"]["datetime"] is None
    assert item.stac["geometry"]["coordinates"] == geometry["coordinates"]
    assert item.stac["geometry"] == geometry
    assert item.stac["bbox"] == bbox
    assert item.stac["assets"]["visual"]["file:checksum"] == checksum
    assert {"rel": "self", "href": f"./{id_}.json", "type": "application/json"} in item.stac["links"]


def test_imagery_add_collection(mocker) -> None:  # type: ignore
    metadata: CollectionTitleMetadata = {
        "category": "Urban Aerial Photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2022, 2, 2),
        "end_datetime": datetime(2022, 2, 2),
        "lifecycle": "completed",
        "location": None,
        "event": None,
        "historic_survey_number": None,
    }
    ulid = "fake_ulid"
    collection = ImageryCollection(title_metadata=metadata, collection_id=ulid)

    path = "./test/BR34_5000_0302.tiff"
    id_ = get_file_name_from_path(path)
    checksum = "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    mocker.patch("scripts.stac.util.checksum.multihash_as_hex", return_value=checksum)
    item = ImageryItem(id_, path)

    item.add_collection(collection.stac["id"])

    assert item.stac["collection"] == ulid
    assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in item.stac["links"]
    assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in item.stac["links"]
