from datetime import datetime
from decimal import Decimal
from os import environ
from typing import Iterator
from unittest.mock import patch

import pytest
from boto3 import client, resource
from moto import mock_aws
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest import CaptureFixture, raises
from pytest_subtests import SubTests

from scripts.collection_from_items import NoItemsError, main
from scripts.datetimes import utc_now
from scripts.files.fs_s3 import write
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.imagery.metadata_constants import CollectionMetadata


@pytest.fixture(name="item", autouse=True)
def setup() -> Iterator[ImageryItem]:
    # Create mocked STAC Item
    with patch.dict(environ, {"GIT_HASH": "any Git hash", "GIT_VERSION": "any Git version"}):
        item = ImageryItem("123", "./scripts/tests/data/empty.tiff", "any GDAL version", utc_now)
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)
    yield item


@mock_aws
def test_should_create_collection_file(item: ImageryItem) -> None:
    # Mock AWS S3
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="stacfiles")
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
    ]
    # Call script's main function
    main(args)

    # Verify collection.json has been created
    resp = boto3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert '"type": "Collection"' in resp["Body"].read().decode("utf-8")


@mock_aws
def test_should_fail_if_collection_has_no_matching_items(
    item: ImageryItem, capsys: CaptureFixture[str], subtests: SubTests
) -> None:
    # Mock AWS S3
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="stacfiles")
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
    ]
    # Call script's main function
    with raises(NoItemsError):
        main(args)

    logs = capsys.readouterr().out

    with subtests.test(msg="Collection IDs do not match"):
        assert f"skipping: {item_collection_id} and {collection_id} do not match" in logs

    assert f"Collection {collection_id} has no items" in logs


@mock_aws
def test_should_not_add_if_not_item(capsys: CaptureFixture[str]) -> None:
    # Mock AWS S3
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="stacfiles")
    collection_id = "abc"
    # Create mocked "existing" Collection
    metadata: CollectionMetadata = {
        "category": "urban-aerial-photos",
        "region": "hawkes-bay",
        "gsd": Decimal("1"),
        "start_datetime": datetime(2023, 9, 20),
        "end_datetime": datetime(2023, 9, 20),
        "lifecycle": "ongoing",
        "event_name": None,
        "geographic_description": None,
        "historic_survey_number": None,
    }
    existing_collection = ImageryCollection(metadata, utc_now, collection_id)
    write("s3://stacfiles/collection.json", dict_to_json_bytes(existing_collection.stac))
    # CLI arguments
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
    ]
    # Call script's main function
    with raises(NoItemsError):
        main(args)

    assert "skipping: not a STAC item" in capsys.readouterr().out


@mock_aws
def test_should_determine_dates_from_items(item: ImageryItem) -> None:
    # Mock AWS S3
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="stacfiles")
    item.add_collection("abc")
    write("s3://stacfiles/item_a.json", dict_to_json_bytes(item.stac))
    item.stac["properties"]["start_datetime"] = "2022-04-12T00:00:00Z"
    item.stac["properties"]["end_datetime"] = "2022-04-12T00:00:00Z"
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
    ]
    # Call script's main function
    main(args)

    # Verify collection.json has been created
    resp = boto3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert "(2021-2022)" in resp["Body"].read().decode("utf-8")
