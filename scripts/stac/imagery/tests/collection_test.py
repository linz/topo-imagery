import json
import os
import tempfile
from shutil import rmtree
from tempfile import mkdtemp

import shapely.geometry
from boto3 import resource
from moto import mock_aws
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest_subtests import SubTests
from shapely.predicates import is_valid

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files.files_helper import ContentType
from scripts.files.fs import read
from scripts.files.fs_s3 import write
from scripts.stac.imagery.capture_area import merge_polygons
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem, STACAsset
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.imagery.tests.generators import any_stac_processing, fixed_now_function
from scripts.stac.util.stac_extensions import StacExtensions
from scripts.tests.datetimes_test import any_epoch_datetime, any_epoch_datetime_string


def test_title_description_id_created_on_init(
    fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests
) -> None:
    fake_collection_metadata["event_name"] = "Forest Assessment"
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Forest Assessment"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    with subtests.test():
        assert collection.stac["title"] == "Hawke's Bay Forest Assessment 0.3m Rural Aerial Photos (2023)"

    with subtests.test():
        assert collection.stac["description"] == (
            "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, "
            "published as a record of the Forest Assessment event."
        )

    with subtests.test():
        assert collection.stac["id"]

    with subtests.test():
        assert collection.stac["linz:region"] == "hawkes-bay"

    with subtests.test():
        assert collection.stac["linz:geographic_description"] == "Hawke's Bay Forest Assessment"

    with subtests.test():
        assert collection.stac["linz:event_name"] == "Forest Assessment"

    with subtests.test():
        assert collection.stac["linz:lifecycle"] == "completed"

    with subtests.test():
        assert collection.stac["linz:geospatial_category"] == "rural-aerial-photos"


def test_id_parsed_on_init(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    id_ = "Parsed-Ulid"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug, id_)
    assert collection.stac["id"] == "Parsed-Ulid"


def test_bbox_updated_from_none(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    collection.update_spatial_extent(bbox)
    assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]


def test_bbox_updated_from_existing(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    # init bbox
    bbox = [174.889641, -41.217532, 174.902344, -41.203521]
    collection.update_spatial_extent(bbox)
    # update bbox
    bbox = [174.917643, -41.211157, 174.922965, -41.205490]
    collection.update_spatial_extent(bbox)

    assert collection.stac["extent"]["spatial"]["bbox"] == [[174.889641, -41.217532, 174.922965, -41.203521]]


def test_interval_updated_from_none(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]


def test_interval_updated_from_existing(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    # init interval
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)
    # update interval
    start_datetime = "2021-02-01T00:00:00Z"
    end_datetime = "2021-02-20T00:00:00Z"
    collection.update_temporal_extent(start_datetime, end_datetime)

    assert collection.stac["extent"]["temporal"]["interval"] == [["2021-01-27T00:00:00Z", "2021-02-20T00:00:00Z"]]


def test_add_item(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests) -> None:
    now = any_epoch_datetime()
    now_string = format_rfc_3339_datetime_string(now)
    collection = ImageryCollection(fake_collection_metadata, fixed_now_function(now), fake_linz_slug)
    asset_created_datetime = any_epoch_datetime_string()
    asset_updated_datetime = any_epoch_datetime_string()
    item = ImageryItem(
        "BR34_5000_0304",
        now_string,
        STACAsset(
            **{
                "href": "any href",
                "file:checksum": "any checksum",
                "created": asset_created_datetime,
                "updated": asset_updated_datetime,
            }
        ),
        any_stac_processing(),
    )
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)

    collection.add_item(item.stac)

    links = collection.stac["links"].copy()

    with subtests.test(msg="File checksum heuristic"):
        # The checksum changes based on the contents
        assert links[1].pop("file:checksum").startswith("1220")

    with subtests.test(msg="Main links content"):
        assert [
            {"href": "./collection.json", "rel": "self", "type": "application/json"},
            {"rel": "item", "href": "./BR34_5000_0304.json", "type": "application/geo+json"},
        ] == links

    with subtests.test():
        assert collection.stac["extent"]["temporal"]["interval"] == [[start_datetime, end_datetime]]

    with subtests.test():
        assert collection.stac["extent"]["spatial"]["bbox"] == [bbox]

    for property_name in ["created", "updated"]:
        with subtests.test(msg=f"collection {property_name}"):
            assert collection.stac[property_name] == now_string

        with subtests.test(msg=f"item properties.{property_name}"):
            assert item.stac["properties"][property_name] == now_string

    with subtests.test(msg="item assets.visual.created"):
        assert item.stac["assets"]["visual"]["created"] == asset_created_datetime

    with subtests.test(msg="item assets.visual.updated"):
        assert item.stac["assets"]["visual"]["updated"] == asset_updated_datetime


def test_write_collection(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    target = mkdtemp()
    collectionObj = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == collectionObj.stac["title"]


def test_write_collection_special_chars(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    target = mkdtemp()
    title = "Manawatū-Whanganui"
    collectionObj = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    collectionObj.stac["title"] = title
    collection_target = os.path.join(target, "collection.json")
    collectionObj.write_to(collection_target)
    collection = json.loads(read(collection_target))
    rmtree(target)

    assert collection["title"] == title


def test_add_providers(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection.add_providers([producer])

    assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_default_provider_roles_are_kept(
    fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests
) -> None:
    # given we are adding a non default role to the default provider
    licensor: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.LICENSOR]}
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime, fake_linz_slug, providers=[producer, licensor]
    )

    with subtests.test(msg="it adds the non default role to the existing default role list"):
        assert {
            "name": "Toitū Te Whenua Land Information New Zealand",
            "roles": ["host", "licensor", "processor"],
        } in collection.stac["providers"]

    with subtests.test(msg="it does not duplicate the default provider"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} not in collection.stac[
            "providers"
        ]


def test_default_provider_is_present(
    fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests
) -> None:
    # given adding a provider
    producer: Provider = {"name": "Maxar", "roles": [ProviderRole.PRODUCER]}
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug, providers=[producer])

    with subtests.test(msg="the default provider is still present"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} in collection.stac[
            "providers"
        ]
    with subtests.test(msg="the new provider is added"):
        assert {"name": "Maxar", "roles": ["producer"]} in collection.stac["providers"]


def test_providers_are_not_duplicated(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    producer: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.PRODUCER]}
    licensor: Provider = {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.LICENSOR]}
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime, fake_linz_slug, providers=[producer, licensor]
    )
    assert len(collection.stac["providers"]) == 1
    assert {
        "name": "Toitū Te Whenua Land Information New Zealand",
        "roles": ["host", "licensor", "processor", "producer"],
    } in collection.stac["providers"]


def test_capture_area_added(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests) -> None:
    """
    TODO: geos 3.12 changes the topology-preserving simplifier to produce stable results; see
    <https://github.com/libgeos/geos/pull/718>. Once we start using geos 3.12 in CI we can delete the values for 3.11
    below.
    """
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
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
    with tempfile.TemporaryDirectory() as tmp_path:
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
        assert (
            collection.stac["assets"]["capture_area"]["description"] == "Boundary of the total capture area for "
            "this collection. Excludes nodata areas in the source data. Geometries are simplified."
        )

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
            "1220ba57cd77defc7fa72e140f4faa0846e8905ae443de04aef99bf381d4650c17a0",  # geos 3.11 - geos 3.12 as yet untested
        )

    with subtests.test():
        assert "file:size" in collection.stac["assets"]["capture_area"]

    with subtests.test():
        assert collection.stac["assets"]["capture_area"]["file:size"] in (269,)  # geos 3.11 - geos 3.12 as yet untested


def test_should_make_valid_capture_area() -> None:
    # Given two touching triangles
    polygons = [
        shapely.geometry.shape(
            {
                "type": "MultiPolygon",
                "coordinates": [[[[0, 0], [0, 1], [1, 1], [0, 0]]]],
            }
        ),
        shapely.geometry.shape(
            {
                "type": "MultiPolygon",
                "coordinates": [[[[1, 0], [2, 2], [1, 2], [1, 0]]]],
            }
        ),
    ]

    capture_area = merge_polygons(polygons, 0.1)
    assert is_valid(capture_area)


def test_event_name_is_present(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    fake_collection_metadata["event_name"] = "Forest Assessment"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    assert "Forest Assessment" == collection.stac["linz:event_name"]


def test_geographic_description_is_present(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Forest Assessment"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    assert "Hawke's Bay Forest Assessment" == collection.stac["linz:geographic_description"]


def test_linz_slug_is_present(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    assert fake_linz_slug == collection.stac["linz:slug"]


@mock_aws
def test_capture_dates_added(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime, fake_linz_slug)
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="flat")
    write("s3://flat/capture-dates.geojson", b"")
    collection.add_capture_dates("s3://flat")
    assert collection.stac["assets"]["capture_dates"] == {
        "href": "./capture-dates.geojson",
        "title": "Capture dates",
        "description": "Boundaries of individual surveys or flight runs that make up the overall collection with the "
        "data collection dates, data source links and other associated metadata, such as producers and licensors, "
        "where available. Excludes nodata areas in the source data. Geometries are simplified.",
        "type": ContentType.GEOJSON,
        "roles": ["metadata"],
        "file:checksum": "1220e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "file:size": 0,
    }
