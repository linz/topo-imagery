from datetime import datetime

from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import BoundingBox, ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.tests.datetimes_test import any_epoch_datetime


def test_imagery_stac_item(mocker: MockerFixture, subtests: SubTests) -> None:
    # mock functions that interact with files
    geometry = {
        "type": "Polygon",
        "coordinates": [[[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    mocker.patch("scripts.files.fs.read", return_value=b"")

    path = "./scripts/tests/data/empty.tiff"
    id_ = get_file_name_from_path(path)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"

    item = ImageryItem(id_, path, any_epoch_datetime, start_datetime, end_datetime, geometry, bbox, "any_collection_id")
    # checks
    with subtests.test():
        assert item.id == id_

    with subtests.test():
        assert item.properties.start_datetime == start_datetime

    with subtests.test():
        assert item.properties.end_datetime == end_datetime

    with subtests.test():
        assert item.properties.datetime is None

    with subtests.test():
        assert item.geometry["coordinates"] == geometry["coordinates"]

    with subtests.test():
        assert item.geometry == geometry

    with subtests.test():
        assert item.bbox == bbox

    with subtests.test():
        assert item.assets["visual"]["file:checksum"] == "1220e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    with subtests.test():
        assert {"rel": "self", "href": f"./{id_}.json", "type": "application/json"} in item.links


# pylint: disable=duplicate-code
def test_imagery_add_collection(mocker: MockerFixture, subtests: SubTests) -> None:
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
    collection = ImageryCollection(metadata=metadata, now=any_epoch_datetime, collection_id=ulid)

    path = "./scripts/tests/data/empty.tiff"
    id_ = get_file_name_from_path(path)
    mocker.patch("scripts.files.fs.read", return_value=b"")
    item = ImageryItem(
        id_,
        path,
        any_epoch_datetime,
        any_epoch_datetime_string(),
        any_epoch_datetime_string(),
        {},
        any_bounding_box(),
        collection.stac["id"],
    )

    with subtests.test():
        assert item.collection_id == ulid

    with subtests.test():
        assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in item.links

    with subtests.test():
        assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in item.links


def any_bounding_box() -> BoundingBox:
    return 1, 2, 3, 4


def any_epoch_datetime_string() -> str:
    return format_rfc_3339_datetime_string(any_epoch_datetime())
