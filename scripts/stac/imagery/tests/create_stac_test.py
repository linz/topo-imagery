import json
from pathlib import Path
from typing import cast

from pytest_subtests import SubTests

from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.create_stac import create_collection, create_item
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.tests.generators import any_multihash_as_hex
from scripts.tests.datetimes_test import any_epoch_datetime_string


def test_create_item_with_derived_from(tmp_path: Path) -> None:
    derived_from_path = tmp_path / "derived_from_item.json"
    fake_item = {
        "type": "Feature",
        "id": "fake_item",
        "properties": {"start_datetime": "2024-09-02T12:00:00Z", "end_datetime": "2024-09-02T12:00:00Z"},
    }
    derived_from_path.write_text(json.dumps(fake_item))
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    item = create_item(
        "./scripts/tests/data/empty.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        any_epoch_datetime_string(),
        fake_gdal_info,
        [derived_from_path.as_posix()],
    )

    assert {
        "href": derived_from_path.as_posix(),
        "rel": "derived_from",
        "type": "application/geo+json",
        "file:checksum": "12209c3d50f21fdd739de5c76b3c7ca60ee7f5cf69c2cf92b1d0136308cf63d9c5d5",
    } in item.stac["links"]


def test_create_item_with_derived_from_datetimes(tmp_path: Path) -> None:
    derived_from_path_a = tmp_path / "derived_from_item_a.json"
    derived_from_path_b = tmp_path / "derived_from_item_b.json"
    fake_item_a = {
        "type": "Feature",
        "id": "fake_item",
        "properties": {"start_datetime": "2024-09-02T12:00:00Z", "end_datetime": "2024-09-02T12:00:00Z"},
    }
    fake_item_b = {
        "type": "Feature",
        "id": "fake_item",
        "properties": {"start_datetime": "1998-02-12T11:00:00Z", "end_datetime": "1999-09-02T12:00:00Z"},
    }
    derived_from_path_a.write_text(json.dumps(fake_item_a))
    derived_from_path_b.write_text(json.dumps(fake_item_b))
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    item = create_item(
        "./scripts/tests/data/empty.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        any_epoch_datetime_string(),
        fake_gdal_info,
        [derived_from_path_a.as_posix(), derived_from_path_b.as_posix()],
    )

    assert item.stac["properties"]["start_datetime"] == "1998-02-12T11:00:00Z"
    assert item.stac["properties"]["end_datetime"] == "2024-09-02T12:00:00Z"


def test_create_item_when_resupplying(subtests: SubTests, tmp_path: Path) -> None:
    item_name = "empty"
    existing_item = tmp_path / f"{item_name}.json"
    tiff_path = f"./scripts/tests/data/{item_name}.tiff"
    created_datetime = "created datetime"
    updated_datetime = "updated datetime"
    existing_item_content = {
        "type": "Feature",
        "id": item_name,
        "assets": {
            "visual": {
                "href": tiff_path,
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "file:checksum": "12205f300ac3bd1d289da1517144d4851050e544c43c58c23ccfcc1f6968f764a45a",
                "created": created_datetime,
                "updated": updated_datetime,
            }
        },
        "properties": {"created": created_datetime, "updated": updated_datetime},
    }

    existing_item.write_text(json.dumps(existing_item_content))
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    current_datetime = "current datetime"
    item = create_item(
        tiff_path,
        "",
        "",
        "abc123",
        "any GDAL version",
        current_datetime,
        fake_gdal_info,
        published_path=tmp_path.as_posix(),
    )

    with subtests.test(msg="properties.created"):
        assert item.stac["properties"]["created"] == created_datetime

    with subtests.test(msg="properties.updated"):
        assert item.stac["properties"]["updated"] == updated_datetime

    with subtests.test(msg="assets.visual.created"):
        assert item.stac["assets"]["visual"]["created"] == created_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.stac["assets"]["visual"]["updated"] == updated_datetime


def test_create_item_when_resupplying_from_incomplete_metadata(subtests: SubTests, tmp_path: Path) -> None:
    # TODO: Remove this test once TDE-1103 is DONE
    item_name = "empty"
    existing_item = tmp_path / f"{item_name}.json"
    existing_item_content = {"type": "Feature", "id": item_name}
    existing_item.write_text(json.dumps(existing_item_content))
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    current_datetime = "current datetime"
    item = create_item(
        f"./scripts/tests/data/{item_name}.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        current_datetime,
        fake_gdal_info,
        published_path=tmp_path.as_posix(),
    )

    with subtests.test("created"):
        assert item.stac["properties"]["created"] == current_datetime

    with subtests.test("updated"):
        assert item.stac["properties"]["updated"] == current_datetime


def test_create_item_when_resupplying_with_new_file(subtests: SubTests, tmp_path: Path) -> None:
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    current_datetime = "current datetime"
    item = create_item(
        "./scripts/tests/data/empty.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        current_datetime,
        fake_gdal_info,
        published_path=tmp_path.as_posix(),
    )

    with subtests.test("created"):
        assert item.stac["properties"]["created"] == current_datetime

    with subtests.test("updated"):
        assert item.stac["properties"]["updated"] == current_datetime


def test_create_item_when_resupplying_with_changed_file(subtests: SubTests, tmp_path: Path) -> None:
    item_name = "empty"
    original_item = tmp_path / f"{item_name}.json"
    asset_file = f"./scripts/tests/data/{item_name}.tiff"
    created_datetime = "created datetime"
    updated_datetime = "updated datetime"
    original_item_content = {
        "type": "Feature",
        "id": item_name,
        "assets": {
            "visual": {
                "href": asset_file,
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "file:checksum": any_multihash_as_hex(),
                "created": created_datetime,
                "updated": updated_datetime,
            }
        },
        "properties": {"created": created_datetime, "updated": updated_datetime},
    }

    original_item.write_text(json.dumps(original_item_content))

    current_datetime = "current datetime"
    item = create_item(
        "./scripts/tests/data/empty.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        current_datetime,
        cast(GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}),
        published_path=tmp_path.as_posix(),
    )

    with subtests.test(msg="assets.visual.created"):
        assert item.stac["assets"]["visual"]["created"] == created_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.stac["assets"]["visual"]["updated"] == current_datetime


def test_create_collection(fake_collection_metadata: CollectionMetadata) -> None:
    collection_id = "test_collection"

    collection = create_collection(
        collection_id=collection_id,
        collection_metadata=fake_collection_metadata,
        producers=[],
        licensors=[],
        stac_items=[],
        item_polygons=[],
        add_capture_dates=False,
        uri="test",
    )

    assert collection.stac["id"] == collection_id
