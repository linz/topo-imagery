from datetime import datetime, timezone

from pystac import RelType
from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import BoundingBox, ImageryItem
from scripts.stac.imagery.links import ComparableLink
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
    start_datetime = datetime(year=2021, month=1, day=27, tzinfo=timezone.utc)
    end_datetime = datetime(year=2021, month=1, day=27, tzinfo=timezone.utc)

    item = ImageryItem(id_, geometry, bbox, any_epoch_datetime, start_datetime, end_datetime, path, "any_collection_id")
    # checks
    with subtests.test():
        assert item.id == id_

    with subtests.test():
        assert item.properties["start_datetime"] == format_rfc_3339_datetime_string(start_datetime)

    with subtests.test():
        assert item.properties["end_datetime"] == format_rfc_3339_datetime_string(end_datetime)

    with subtests.test():
        assert item.datetime is None

    with subtests.test():
        assert item.geometry is not None
        assert item.geometry.get("coordinates") == geometry["coordinates"]

    with subtests.test():
        assert item.geometry == geometry

    with subtests.test():
        assert item.bbox == list(bbox)

    with subtests.test():
        assert (
            getattr(item.assets["visual"], "file:checksum")
            == "1220e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    with subtests.test():
        assert ComparableLink(RelType.SELF, f"./{id_}.json", "application/json") in item.links


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
        {},
        any_bounding_box(),
        any_epoch_datetime,
        any_epoch_datetime(),
        any_epoch_datetime(),
        path,
        collection.stac["id"],
    )

    with subtests.test():
        assert item.collection_id == ulid

    with subtests.test():
        assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in [
            link.to_dict() for link in item.links
        ]

    with subtests.test():
        assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in [
            link.to_dict() for link in item.links
        ]


def any_bounding_box() -> BoundingBox:
    return 1, 2, 3, 4
