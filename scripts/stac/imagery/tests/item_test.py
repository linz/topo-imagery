import json
from datetime import datetime
from decimal import Decimal
from os import environ
from pathlib import Path
from typing import Any
from unittest.mock import patch

from pytest_subtests import SubTests

from scripts.files.files_helper import get_file_name_from_path
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.tests.generators import any_stac_asset, any_stac_processing
from scripts.stac.link import Relation
from scripts.stac.util.media_type import StacMediaType
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
                    "rel": Relation.SELF,
                    "type": StacMediaType.GEOJSON,
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


def test_create_item_from_file(tmp_path: Path, fake_imagery_item_stac: dict[str, Any]) -> None:
    temp_file = tmp_path / "existing_item.json"
    temp_file.write_text(json.dumps(fake_imagery_item_stac))
    imagery_item = ImageryItem.from_file(str(temp_file))

    assert imagery_item.stac == fake_imagery_item_stac


def test_update_item_checksum(subtests: SubTests, tmp_path: Path, fake_imagery_item_stac: dict[str, Any]) -> None:
    temp_file = tmp_path / "existing_item.json"
    temp_file.write_text(json.dumps(fake_imagery_item_stac))

    existing_checksum = fake_imagery_item_stac["assets"]["visual"]["file:checksum"]

    new_stac_processing = any_stac_processing()
    new_updated_date = new_stac_processing["processing:datetime"]
    new_stac_properties = fake_imagery_item_stac["properties"].copy()
    new_stac_properties.update(new_stac_processing)
    new_checksum = "my_new_checksum"

    imagery_item = ImageryItem.from_file(str(temp_file))

    imagery_item.update_checksum_related_metadata(existing_checksum, new_stac_processing)
    with subtests.test(msg="item.stac should not change when checksum did not change"):
        assert imagery_item.stac == fake_imagery_item_stac

    with subtests.test(msg="item.stac checksum changes to newly supplied checksum"):
        imagery_item.update_checksum_related_metadata(new_checksum, new_stac_processing)
        assert imagery_item.stac["assets"]["visual"]["file:checksum"] == new_checksum

        assert imagery_item.stac["assets"]["visual"]["updated"] == new_updated_date
        assert imagery_item.stac["properties"]["updated"] == new_updated_date

        assert imagery_item.stac["properties"] == new_stac_properties


# pylint: disable=duplicate-code
def test_imagery_add_collection(fake_linz_slug: str, subtests: SubTests) -> None:
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
    collection = ImageryCollection(metadata=metadata, now=any_epoch_datetime, linz_slug=fake_linz_slug, collection_id=ulid)

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
