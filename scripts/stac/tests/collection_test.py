import json
import os
from datetime import datetime
from shutil import rmtree
from tempfile import mkdtemp
from typing import Generator

import pytest

from scripts.files.fs import read
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionTitleMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole


@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[CollectionTitleMetadata, None, None]:
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
    yield metadata


def test_title_description_id_created_on_init(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    assert collection.stac["title"] == "Auckland 0.3m Urban Aerial Photos (2022)"
    assert collection.stac["description"] == "Orthophotography within the Auckland region captured in the 2022 flying season."
    assert collection.stac["id"]


def test_id_parsed_on_init(metadata: CollectionTitleMetadata) -> None:
    id_ = "Parsed-Ulid"
    collection = ImageryCollection(metadata, id_)
    assert collection.stac["id"] == "Parsed-Ulid"


def test_bbox_updated_from_none(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    collection.update_spatial_extent(bbox)
    assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]


def test_bbox_updated_from_existing(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    # init bbox
    bbox = [174.889641, -41.217532, 174.902344, -41.203521]
    collection.update_spatial_extent(bbox)
    # update bbox
    bbox = [174.917643, -41.211157, 174.922965, -41.205490]
    collection.update_spatial_extent(bbox)

    assert collection.stac["extent"]["spatial"]["bbox"] == [[174.889641, -41.217532, 174.922965, -41.203521]]


def test_interval_updated_from_none(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]


def test_interval_updated_from_existing(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    # init interval
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    # update interval
    start_datetime = "2021-02-01T00:00:00Z"
    end_datetime = "2021-02-20T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)

    assert collection.stac["extent"]["temporal"]["interval"] == [["2021-01-27T00:00:00Z", "2021-02-20T00:00:00Z"]]


def test_add_item(mocker, metadata: CollectionTitleMetadata) -> None:  # type: ignore
    collection = ImageryCollection(metadata)
    checksum = "1220cdef68d62fb912110b810e62edc53de07f7a44fb2b310db700e9d9dd58baa6b4"
    mocker.patch("scripts.stac.util.checksum.multihash_as_hex", return_value=checksum)
    item = ImageryItem("BR34_5000_0304", "./test/BR34_5000_0304.tiff")
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    start_datetime = "2021-01-27 00:00:00Z"
    end_datetime = "2021-01-27 00:00:00Z"
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)

    collection.add_item(item.stac)

    assert {"rel": "item", "href": "./BR34_5000_0304.json", "type": "application/json"} in collection.stac["links"]
    assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]
    assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]


def test_write_collection(metadata: CollectionTitleMetadata) -> None:
    target = mkdtemp()
    collectionObj = ImageryCollection(metadata)
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == collectionObj.stac["title"]


def test_write_collection_special_chars(metadata: CollectionTitleMetadata) -> None:
    target = mkdtemp()
    title = "Manawatū-Whanganui"
    collectionObj = ImageryCollection(metadata)
    collectionObj.stac["title"] = title
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == title


def test_add_providers(metadata: CollectionTitleMetadata) -> None:
    collection = ImageryCollection(metadata)
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection.add_providers([producer])

    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_default_provider_roles_are_kept(metadata: CollectionTitleMetadata) -> None:
    # given we are adding a non default role to the default provider
    licensor: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.LICENSOR]}
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(metadata, providers=[producer, licensor])

    # then it adds the non default role to the existing default role list
    assert {
        "name": "Toitū Te Whenua Land Information New Zealand",
        "roles": ["licensor", "host", "processor"],
    } in collection.stac["providers"]
    # then it does not duplicate the default provider
    assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} not in collection.stac[
        "providers"
    ]


def test_default_provider_is_present(metadata: CollectionTitleMetadata) -> None:
    # given adding a provider
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(metadata, providers=[producer])

    # then the default provider is still present
    assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} in collection.stac[
        "providers"
    ]
    # then the new provider is added
    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]
