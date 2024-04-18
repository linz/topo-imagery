from datetime import datetime

from pytest_subtests import SubTests

from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata


def test_imagery_stac_item(mocker, subtests: SubTests) -> None:  # type: ignore
    # mock functions that interact with files
    geometry = {
        "type": "Polygon",
        "coordinates": [[[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    mocker.patch("scripts.files.fs.read", return_value=b"")

    path = "./test/BR34_5000_0302.tiff"
    id_ = get_file_name_from_path(path)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"

    item = ImageryItem(id_, path)
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)
    # checks
    with subtests.test():
        assert item.stac["id"] == id_

    with subtests.test():
        assert item.stac["properties"]["start_datetime"] == start_datetime

    with subtests.test():
        assert item.stac["properties"]["end_datetime"] == end_datetime

    with subtests.test():
        assert item.stac["properties"]["datetime"] is None

    with subtests.test():
        assert item.stac["geometry"]["coordinates"] == geometry["coordinates"]

    with subtests.test():
        assert item.stac["geometry"] == geometry

    with subtests.test():
        assert item.stac["bbox"] == bbox

    with subtests.test():
        assert (
            item.stac["assets"]["visual"]["file:checksum"]
            == "1220e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    with subtests.test():
        assert {"rel": "self", "href": f"./{id_}.json", "type": "application/json"} in item.stac["links"]


# pylint: disable=duplicate-code
def test_imagery_add_collection(mocker, subtests: SubTests) -> None:  # type: ignore
    metadata: CollectionMetadata = {
        "category": "urban-aerial-photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2022, 2, 2),
        "end_datetime": datetime(2022, 2, 2),
        "lifecycle": "completed",
        "event_name": None,
        "historic_survey_number": None,
        "geographic_description": None,
    }
    ulid = "fake_ulid"
    collection = ImageryCollection(metadata=metadata, collection_id=ulid)

    path = "./test/BR34_5000_0302.tiff"
    id_ = get_file_name_from_path(path)
    mocker.patch("scripts.files.fs.read", return_value=b"")
    item = ImageryItem(id_, path)

    item.add_collection(collection.stac["id"])

    with subtests.test():
        assert item.stac["collection"] == ulid

    with subtests.test():
        assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in item.stac["links"]

    with subtests.test():
        assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in item.stac["links"]
