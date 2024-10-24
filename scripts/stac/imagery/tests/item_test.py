from datetime import datetime
from decimal import Decimal
from os import environ
from unittest.mock import patch

from pytest_subtests import SubTests

from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.tests.generators import any_stac_asset, any_stac_processing
from scripts.tests.datetimes_test import any_epoch_datetime


def test_imagery_stac_item(subtests: SubTests) -> None:
    # mock functions that interact with files
    geometry = {
        "type": "Polygon",
        "coordinates": [[[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)

    path = "./scripts/tests/data/empty.tiff"
    id_ = get_file_name_from_path(path)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-29T00:00:00Z"

    git_hash = "any Git hash"
    git_version = "any Git version string"
    asset = any_stac_asset()
    stac_processing = any_stac_processing()
    with patch.dict(environ, {"GIT_HASH": git_hash, "GIT_VERSION": git_version}):
        item = ImageryItem(id_, asset, stac_processing)
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)

    # checks
    with subtests.test():
        assert item.stac == {
            "assets": {
                "visual": {**asset, "type": "image/tiff; application=geotiff; profile=cloud-optimized"},
            },
            "bbox": bbox,
            "geometry": geometry,
            "id": id_,
            "links": [
                {
                    "href": "./empty.json",
                    "rel": "self",
                    "type": "application/geo+json",
                },
            ],
            "properties": {
                "created": asset["created"],
                "datetime": None,
                "end_datetime": end_datetime,
                "start_datetime": start_datetime,
                "updated": asset["updated"],
                **stac_processing,
            },
            "stac_extensions": [
                "https://stac-extensions.github.io/file/v2.0.0/schema.json",
                "https://stac-extensions.github.io/processing/v1.2.0/schema.json",
            ],
            "stac_version": "1.0.0",
            "type": "Feature",
        }


# pylint: disable=duplicate-code
def test_imagery_add_collection(subtests: SubTests) -> None:
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
    item = ImageryItem(id_, any_stac_asset(), any_stac_processing())

    item.add_collection(collection.stac["id"])

    with subtests.test():
        assert item.stac["collection"] == ulid

    with subtests.test():
        assert {"rel": "collection", "href": "./collection.json", "type": "application/json"} in item.stac["links"]

    with subtests.test():
        assert {"rel": "parent", "href": "./collection.json", "type": "application/json"} in item.stac["links"]
