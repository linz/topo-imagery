import json
import os
from shutil import rmtree
from tempfile import mkdtemp
from typing import Generator

import pytest

from scripts.files.fs import read
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.provider import Provider, ProviderRole


@pytest.fixture(name="setup_collection", autouse=True)
def setup() -> Generator[ImageryCollection, None, None]:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)
    yield collection


def test_title_description_id_created_on_init() -> None:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)
    assert collection.stac["title"] == "Test Urban Imagery"
    assert collection.stac["description"] == "Test Urban Imagery Description"
    assert collection.stac["id"]


def test_id_parsed_on_init() -> None:
    title = "Test"
    description = "Test"
    id_ = "Parsed-Ulid"
    collection = ImageryCollection(title, description, id_)
    assert collection.stac["id"] == "Parsed-Ulid"


def test_bbox_updated_from_none(setup_collection: ImageryCollection) -> None:
    collection = setup_collection
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    collection.update_spatial_extent(bbox)
    assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]


def test_bbox_updated_from_existing(setup_collection: ImageryCollection) -> None:
    collection = setup_collection
    # init bbox
    bbox = [174.889641, -41.217532, 174.902344, -41.203521]
    collection.update_spatial_extent(bbox)
    # update bbox
    bbox = [174.917643, -41.211157, 174.922965, -41.205490]
    collection.update_spatial_extent(bbox)

    assert collection.stac["extent"]["spatial"]["bbox"] == [[174.889641, -41.217532, 174.922965, -41.203521]]


def test_interval_updated_from_none(setup_collection: ImageryCollection) -> None:
    collection = setup_collection
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]


def test_interval_updated_from_existing(setup_collection: ImageryCollection) -> None:
    collection = setup_collection
    # init interval
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    # update interval
    start_datetime = "2021-02-01T00:00:00Z"
    end_datetime = "2021-02-20T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)

    assert collection.stac["extent"]["temporal"]["interval"] == [["2021-01-27T00:00:00Z", "2021-02-20T00:00:00Z"]]


def test_add_item(mocker, setup_collection: ImageryCollection) -> None:  # type: ignore
    collection = setup_collection
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


def test_write_collection(setup_collection: ImageryCollection) -> None:
    target = mkdtemp()
    collection_target = os.path.join(target, "collection.json")
    setup_collection.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == setup_collection.stac["title"]


def test_write_collection_special_chars(setup_collection: ImageryCollection) -> None:
    target = mkdtemp()
    title = "Manawatū-Whanganui"
    setup_collection.stac["title"] = title
    collection_target = os.path.join(target, "collection.json")
    setup_collection.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == title


def test_add_providers(setup_collection: ImageryCollection) -> None:
    collection = setup_collection
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection.add_providers([producer])

    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_default_provider_present() -> None:
    licensor: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.LICENSOR]}
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description, providers=[producer, licensor])

    assert {
        "name": "Toitū Te Whenua Land Information New Zealand",
        "roles": ["licensor", "host", "processor"],
    } in collection.stac["providers"]
    assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} not in collection.stac[
        "providers"
    ]


def test_default_provider_missing() -> None:
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description, providers=[producer])

    assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} in collection.stac[
        "providers"
    ]
    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]
