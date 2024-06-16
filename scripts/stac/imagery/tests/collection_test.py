import json
import os
from datetime import datetime, timezone
from shutil import rmtree
from tempfile import TemporaryDirectory, mkdtemp
from typing import Callable, Generator

import pytest
import shapely.geometry
from pytest_subtests import SubTests

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files.fs import read
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.util.stac_extensions import StacExtensions
from scripts.tests.datetimes_test import any_epoch_datetime


# pylint: disable=duplicate-code
@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[CollectionMetadata, None, None]:
    metadata: CollectionMetadata = {
        "category": "urban-aerial-photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2022, 2, 2),
        "end_datetime": datetime(2022, 2, 2),
        "lifecycle": "completed",
        "event_name": "Forest Assessment",
        "historic_survey_number": None,
        "geographic_description": "Auckland North Forest Assessment",
    }
    yield metadata


def test_title_description_id_created_on_init(metadata: CollectionMetadata, subtests: SubTests) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    with subtests.test():
        assert collection.stac["title"] == "Auckland North Forest Assessment 0.3m Urban Aerial Photos (2022)"

    with subtests.test():
        assert (
            collection.stac["description"]
            == "Orthophotography within the Auckland region captured in the 2022 flying season, published as a record of the Forest Assessment event."  # pylint: disable=line-too-long
        )

    with subtests.test():
        assert collection.stac["id"]

    with subtests.test():
        assert collection.stac["linz:region"] == "auckland"

    with subtests.test():
        assert collection.stac["linz:geographic_description"] == "Auckland North Forest Assessment"

    with subtests.test():
        assert collection.stac["linz:event_name"] == "Forest Assessment"

    with subtests.test():
        assert collection.stac["linz:lifecycle"] == "completed"

    with subtests.test():
        assert collection.stac["linz:geospatial_category"] == "urban-aerial-photos"


def test_id_parsed_on_init(metadata: CollectionMetadata) -> None:
    id_ = "Parsed-Ulid"
    collection = ImageryCollection(metadata, any_epoch_datetime, id_)
    assert collection.stac["id"] == "Parsed-Ulid"


def test_bbox_updated_from_none(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    collection.update_spatial_extent(bbox)
    assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]


def test_bbox_updated_from_existing(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    # init bbox
    bbox = (174.889641, -41.217532, 174.902344, -41.203521)
    collection.update_spatial_extent(bbox)
    # update bbox
    bbox = (174.917643, -41.211157, 174.922965, -41.205490)
    collection.update_spatial_extent(bbox)

    assert collection.stac["extent"]["spatial"]["bbox"] == [(174.889641, -41.217532, 174.922965, -41.203521)]


def test_interval_updated_from_none(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]


def test_interval_updated_from_existing(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    # init interval
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    # update interval
    start_datetime = "2021-02-01T00:00:00Z"
    end_datetime = "2021-02-20T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)

    assert collection.stac["extent"]["temporal"]["interval"] == [["2021-01-27T00:00:00Z", "2021-02-20T00:00:00Z"]]


def fixed_now_function(now: datetime) -> Callable[[], datetime]:
    def func() -> datetime:
        return now

    return func


def test_add_item(metadata: CollectionMetadata, subtests: SubTests) -> None:
    now = any_epoch_datetime()
    now_function = fixed_now_function(now)
    collection = ImageryCollection(metadata, now_function)
    item_file_path = "./scripts/tests/data/empty.tiff"
    modified_datetime = datetime(2001, 2, 3, hour=4, minute=5, second=6, tzinfo=timezone.utc)
    os.utime(item_file_path, times=(any_epoch_datetime().timestamp(), modified_datetime.timestamp()))
    start_datetime = end_datetime = datetime(2021, 1, 27, tzinfo=timezone.utc)
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    item = ImageryItem(
        "BR34_5000_0304", geometry, bbox, now_function, start_datetime, end_datetime, item_file_path, collection.stac["id"]
    )

    collection.add_item(item)

    links = collection.stac["links"].copy()

    with subtests.test(msg="File checksum heuristic"):
        # The checksum changes based on the contents
        assert links[1].pop("file:checksum").startswith("1220")

    with subtests.test(msg="Main links content"):
        assert [
            {"rel": "self", "href": "./collection.json", "type": "application/json"},
            {"rel": "item", "href": "./BR34_5000_0304.json", "type": "application/json"},
        ] == links

    with subtests.test():
        assert collection.stac["extent"]["temporal"]["interval"] == [
            [format_rfc_3339_datetime_string(start_datetime), format_rfc_3339_datetime_string(start_datetime)]
        ]

    with subtests.test():
        assert collection.stac["extent"]["spatial"]["bbox"] == [list(bbox)]

    now_string = format_rfc_3339_datetime_string(now)
    for property_name in ["created", "updated"]:
        with subtests.test(msg=f"collection {property_name}"):
            assert collection.stac[property_name] == now_string

        with subtests.test(msg=f"item assets.visual.{property_name}"):
            assert getattr(item.assets["visual"], property_name) == "2001-02-03T04:05:06Z"

    with subtests.test(msg="item properties.created"):
        assert item.properties["created"] == now_string

    with subtests.test(msg="item properties.updated"):
        assert item.properties["updated"] == now_string


def test_write_collection(metadata: CollectionMetadata) -> None:
    target = mkdtemp()
    collectionObj = ImageryCollection(metadata, any_epoch_datetime)
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == collectionObj.stac["title"]


def test_write_collection_special_chars(metadata: CollectionMetadata) -> None:
    target = mkdtemp()
    title = "Manawatū-Whanganui"
    collectionObj = ImageryCollection(metadata, any_epoch_datetime)
    collectionObj.stac["title"] = title
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == title


def test_add_providers(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection.add_providers([producer])

    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_default_provider_roles_are_kept(metadata: CollectionMetadata, subtests: SubTests) -> None:
    # given we are adding a non default role to the default provider
    licensor: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.LICENSOR]}
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(metadata, any_epoch_datetime, providers=[producer, licensor])

    with subtests.test(msg="it adds the non default role to the existing default role list"):
        assert {
            "name": "Toitū Te Whenua Land Information New Zealand",
            "roles": ["licensor", "host", "processor"],
        } in collection.stac["providers"]

    with subtests.test(msg="it does not duplicate the default provider"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} not in collection.stac[
            "providers"
        ]


def test_default_provider_is_present(metadata: CollectionMetadata, subtests: SubTests) -> None:
    # given adding a provider
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(metadata, any_epoch_datetime, providers=[producer])

    with subtests.test(msg="the default provider is still present"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} in collection.stac[
            "providers"
        ]
    with subtests.test(msg="the new provider is added"):
        assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_capture_area_added(metadata: CollectionMetadata, subtests: SubTests) -> None:
    """
    TODO: geos 3.12 changes the topology-preserving simplifier to produce stable results; see
    <https://github.com/libgeos/geos/pull/718>. Once we start using geos 3.12 in CI we can delete the values for 3.11
    below.
    """
    collection = ImageryCollection(metadata, any_epoch_datetime)
    file_name = "capture-area.geojson"

    polygons = []
    polygons.append(
        shapely.geometry.shape(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [178.259659571653, -38.40831927359251],
                            [178.26012930415902, -38.41478071250544],
                            [178.26560430668172, -38.41453416326152],
                            [178.26513409076952, -38.40807278109057],
                            [178.259659571653, -38.40831927359251],
                        ]
                    ]
                ],
            }
        )
    )
    polygons.append(
        shapely.geometry.shape(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [178.25418498567294, -38.40856551170436],
                            [178.25465423474975, -38.41502700730107],
                            [178.26012930415902, -38.41478071250544],
                            [178.259659571653, -38.40831927359251],
                            [178.25418498567294, -38.40856551170436],
                        ]
                    ]
                ],
            }
        )
    )
    with TemporaryDirectory() as tmp_path:
        artifact_path = os.path.join(tmp_path, "tmp")
        collection.add_capture_area(polygons, tmp_path, artifact_path)
        file_target = os.path.join(tmp_path, file_name)
        file_artifact = os.path.join(artifact_path, file_name)
        with subtests.test():
            assert os.path.isfile(file_target)

        with subtests.test():
            assert os.path.isfile(file_artifact)

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["href"] == f"./{file_name}"

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["title"] == "Capture area"

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["type"] == "application/geo+json"

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["roles"] == ["metadata"]

    with subtests.test():
        assert StacExtensions.file.value in collection.stac["stac_extensions"]

    with subtests.test():
        assert "file:checksum" in collection.stac["assets"]["capture_area"]

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["file:checksum"] in (
            "1220b15694be7495af38e0f70af67cfdc4f19b8bc415a2eb77d780e7a32c6e5b42c2",  # geos 3.11
            "122040fc8700d5d2d04600f730e10677b19d33f3b1e43b02c7867f4cfc2101930863",  # geos 3.12
        )

    with subtests.test():
        assert "file:size" in collection.stac["assets"]["capture_area"]

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["file:size"] in (
            339,  # geos 3.11
            299,  # geos 3.12
        )


def test_event_name_is_present(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    assert "Forest Assessment" == collection.stac["linz:event_name"]


def test_geographic_description_is_present(metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(metadata, any_epoch_datetime)
    assert "Auckland North Forest Assessment" == collection.stac["linz:geographic_description"]
