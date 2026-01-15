import json
from os import environ
from typing import TYPE_CHECKING, Iterator
from unittest.mock import patch

import pytest
from boto3 import client
from moto import mock_aws
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest import CaptureFixture, raises
from pytest_subtests import SubTests

from scripts.collection_from_items import NoItemsError, main
from scripts.conftest import any_epoch_datetime_string
from scripts.files.fs_s3 import write
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.collection_context import CollectionContext
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.tests.generators import any_stac_asset, any_stac_processing

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = GetObjectOutputTypeDef = dict


@pytest.fixture(name="item", autouse=True)
def setup() -> Iterator[ImageryItem]:
    # Create mocked STAC Item
    with patch.dict(environ, {"GIT_HASH": "any Git hash", "GIT_VERSION": "any Git version"}):
        item = ImageryItem("123", any_stac_asset(), any_stac_processing())
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    start_datetime = "2021-01-27T11:00:00Z"
    end_datetime = "2021-01-27T11:00:00Z"
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)
    yield item


@mock_aws
def test_should_create_collection_file(item: ImageryItem, fake_collection_context: CollectionContext) -> None:
    # Mock AWS S3
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))
    # CLI arguments
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--linz-slug",
        fake_collection_context.linz_slug,
    ]
    # Call script's main function
    main(args)

    # Verify collection.json has been created
    resp = s3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert '"type": "Collection"' in resp["Body"].read().decode("utf-8")


@mock_aws
def test_should_create_coastal_collection_file(item: ImageryItem, fake_collection_context: CollectionContext) -> None:
    # Mock AWS S3
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))
    # CLI arguments
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "dem",
        "--domain",
        "coastal",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--linz-slug",
        fake_collection_context.linz_slug,
    ]
    # Call script's main function
    main(args)

    # Verify collection.json has been created with "Coastal" information
    resp = s3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert "Coastal" in resp["Body"].read().decode("utf-8")


@mock_aws
def test_should_fail_if_collection_has_no_matching_items(
    item: ImageryItem, fake_collection_context: CollectionContext, capsys: CaptureFixture[str], subtests: SubTests
) -> None:
    # Mock AWS S3
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item_collection_id = "abc"
    item.add_collection(item_collection_id)
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))
    # CLI arguments
    # collection ID is `def` <> `abc`
    collection_id = "def"
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        collection_id,
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--current-datetime",
        any_epoch_datetime_string(),
        "--linz-slug",
        fake_collection_context.linz_slug,
    ]
    # Call script's main function
    with raises(NoItemsError):
        main(args)

    logs = capsys.readouterr().out

    with subtests.test(msg="Collection IDs do not match"):
        assert f"skipping: {item_collection_id} and {collection_id} do not match" in logs

    assert f"Collection {collection_id} has no items" in logs


def test_should_fail_to_create_collection_file_without_linz_slug(capsys: CaptureFixture[str]) -> None:
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
    ]
    # Call script's main function
    with raises(SystemExit):
        main(args)
    assert "the following arguments are required: --linz-slug" in capsys.readouterr().err


@mock_aws
def test_should_not_add_if_not_item(fake_collection_context: CollectionContext, capsys: CaptureFixture[str]) -> None:
    # Mock AWS S3
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    # Create mocked "existing" Collection
    existing_collection = ImageryCollection(fake_collection_context, any_epoch_datetime_string(), any_epoch_datetime_string())
    write("s3://stacfiles/collection.json", dict_to_json_bytes(existing_collection.stac))
    assert fake_collection_context.collection_id is not None
    # CLI arguments
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        fake_collection_context.collection_id,
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--current-datetime",
        any_epoch_datetime_string(),
        "--linz-slug",
        fake_collection_context.linz_slug,
    ]
    # Call script's main function
    with raises(NoItemsError):
        main(args)

    assert "skipping: not a STAC item" in capsys.readouterr().out


@mock_aws
def test_should_determine_dates_from_items(item: ImageryItem, fake_collection_context: CollectionContext) -> None:
    # Mock AWS S3
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item_a.json", dict_to_json_bytes(item.stac))
    item.stac["properties"]["start_datetime"] = "2022-04-12T12:00:00Z"
    item.stac["properties"]["end_datetime"] = "2022-04-12T12:00:00Z"
    write("s3://stacfiles/item_b.json", dict_to_json_bytes(item.stac))

    # CLI arguments
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--current-datetime",
        any_epoch_datetime_string(),
        "--linz-slug",
        fake_collection_context.linz_slug,
    ]
    # Call script's main function
    main(args)

    # Verify collection.json has been created
    resp = s3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert "(2021-2022)" in resp["Body"].read().decode("utf-8")


@mock_aws
def test_should_accept_simplified_capture_area_flag(item: ImageryItem, fake_collection_context: CollectionContext) -> None:
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))

    footprint = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [178.259659571653, -38.40831927359251],
                            [178.26012930415902, -38.41478071250544],
                            [178.26560430668172, -38.41453416326152],
                            [178.26513409076952, -38.40807278109057],
                            [178.259659571653, -38.40831927359251],
                        ]
                    ],
                },
            }
        ],
    }
    write("s3://stacfiles/item_footprint.geojson", dict_to_json_bytes(footprint))

    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--linz-slug",
        fake_collection_context.linz_slug,
        "--supplied-capture-area",
        "",
        "--simplified-capture-area",
        "true",
    ]
    main(args)

    resp = s3_client.get_object(Bucket="stacfiles", Key="collection.json")
    collection_content = resp["Body"].read().decode("utf-8")
    collection_json = json.loads(collection_content)

    assert "capture_area" in collection_json["assets"]
    expected_description = (
        "Boundary of the total capture area for this collection. "
        "May include some areas of nodata where capture was attempted but unsuccessful. "
        "Geometries are simplified."
    )
    assert collection_json["assets"]["capture_area"]["description"] == expected_description


@mock_aws
def test_should_fail_with_both_supplied_and_simplified_capture_area(
    item: ImageryItem, fake_collection_context: CollectionContext, capsys: CaptureFixture[str]
) -> None:
    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))
    write("s3://stacfiles/supplied-capture-area.geojson", dict_to_json_bytes({"type": "FeatureCollection", "features": []}))

    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
        "--linz-slug",
        fake_collection_context.linz_slug,
        "--supplied-capture-area",
        "s3://stacfiles/supplied-capture-area.geojson",
        "--simplified-capture-area",
        "true",
    ]

    with raises(SystemExit):
        main(args)

    assert "--simplified-capture-area cannot be True when --supplied-capture-area is set." in capsys.readouterr().err
