from datetime import datetime, timezone
from decimal import Decimal
from os import environ
from unittest.mock import patch

from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.util.stac_extensions import StacExtensions
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

    def fake_now() -> datetime:
        return datetime(1979, 1, 1, tzinfo=timezone.utc)

    git_hash = "any Git hash"
    git_version = "any Git version string"
    gdal_version_string = "any GDAL version string"
    with patch.dict(environ, {"GIT_HASH": git_hash, "GIT_VERSION": git_version}):
        item = ImageryItem(id_, path, gdal_version_string, fake_now)
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
        assert (
            item.stac["properties"]["created"]
            == item.stac["properties"]["updated"]
            == item.stac["properties"]["processing:datetime"]
            == "1979-01-01T00:00:00Z"
        )

    with subtests.test():
        assert item.stac["properties"]["processing:version"] == git_version

    with subtests.test():
        assert item.stac["properties"]["processing:software"] == {
            "gdal": gdal_version_string,
            "linz/topo-imagery": f"https://github.com/linz/topo-imagery/commit/{git_hash}",
        }

    with subtests.test():
        assert item.stac["stac_extensions"] == [StacExtensions.file.value, StacExtensions.processing.value]

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
        assert {"rel": "self", "href": f"./{id_}.json", "type": "application/geo+json"} in item.stac["links"]


# pylint: disable=duplicate-code
def test_imagery_add_collection(mocker: MockerFixture, subtests: SubTests) -> None:
    metadata: CollectionMetadata = {
        "category": "urban-aerial-photos",
        "region": "auckland",
        "gsd": Decimal("0.3"),
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
    item = ImageryItem(id_, path, "any GDAL version", any_epoch_datetime)

    item.add_collection(collection.stac["id"])

    with subtests.test():
        assert item.stac["collection"] == ulid

    with subtests.test():
        assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in item.stac["links"]

    with subtests.test():
        assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in item.stac["links"]


def test_should_set_fallback_version_strings(subtests: SubTests) -> None:
    item = ImageryItem("any ID", "./scripts/tests/data/empty.tiff", "any GDAL version", any_epoch_datetime)

    with subtests.test():
        assert item.stac["properties"]["processing:software"]["linz/topo-imagery"] == "GIT_HASH not specified"

    with subtests.test():
        assert item.stac["properties"]["processing:version"] == "GIT_VERSION not specified"
