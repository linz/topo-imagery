import json
from datetime import timedelta
from pathlib import Path
from typing import cast

from pystac import Link, MediaType, RelType
from pytest_subtests import SubTests

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.create_stac import create_collection, create_item
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.tests.generators import any_multihash_as_hex
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.tests.datetimes_test import any_epoch_datetime, any_epoch_datetime_string


def test_create_item(subtests: SubTests) -> None:
    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )
    current_datetime = any_epoch_datetime_string()
    item = create_item(
        "./scripts/tests/data/empty.tiff",
        "",
        "",
        "abc123",
        "any GDAL version",
        current_datetime,
        fake_gdal_info,
    )

    with subtests.test(msg="properties.created"):
        assert item.properties["created"] == current_datetime

    with subtests.test(msg="properties.updated"):
        assert item.properties["updated"] == current_datetime

    with subtests.test(msg="assets.visual.created"):
        assert item.assets["visual"]["created"] == current_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.assets["visual"]["updated"] == current_datetime


def test_create_item_when_resupplying(subtests: SubTests, tmp_path: Path) -> None:
    item_name = "empty"
    existing_item = tmp_path / f"{item_name}.json"
    tiff_path = f"./scripts/tests/data/{item_name}.tiff"
    derived_from_path = "./scripts/tests/data/fake_item.json"
    created_datetime = "created datetime"
    updated_datetime = "updated datetime"
    links = [
        {
            "href": derived_from_path,
            "rel": "derived_from",
            "type": "application/geo+json",
            "file:checksum": "1220f33d983b9c84d3d0c44f37f4a1b842295a960abcdd3889b898f42988f9e93604",
        },
        {
            "href": "path/to/an/old/derived_from",
            "rel": "derived_from",
            "type": "application/geo+json",
            "file:checksum": "123",
        },
    ]
    existing_item_content = {
        "type": "Feature",
        "id": item_name,
        "links": links,
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
        derived_from=[derived_from_path],
        odr_url=tmp_path.as_posix(),
    )

    with subtests.test(msg="properties.created"):
        assert item.properties["created"] == created_datetime

    with subtests.test(msg="properties.updated"):
        assert item.properties["updated"] == current_datetime

    with subtests.test(msg="assets.visual.created"):
        assert item.assets["visual"].extra_fields["created"] == created_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.assets["visual"].extra_fields["updated"] == updated_datetime

    with subtests.test(msg="links"):
        assert len(item.links) == 3


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
        odr_url=tmp_path.as_posix(),
    )

    with subtests.test(msg="assets.visual.created"):
        assert item.assets["visual"].extra_fields["created"] == created_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.assets["visual"].extra_fields["updated"] == current_datetime


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
        "any current datetime",
        fake_gdal_info,
        [derived_from_path.as_posix()],
    )

    expected_link = Link(
        derived_from_path.as_posix(),
        RelType.DERIVED_FROM,
        MediaType.JSON,
        extra_fields={"file:checksum": "12209c3d50f21fdd739de5c76b3c7ca60ee7f5cf69c2cf92b1d0136308cf63d9c5d5"},
    )
    assert expected_link in item.links


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
        "any current datetime",
        fake_gdal_info,
        [derived_from_path_a.as_posix(), derived_from_path_b.as_posix()],
    )

    assert item.properties["start_datetime"] == "1998-02-12T11:00:00Z"
    assert item.properties["end_datetime"] == "2024-09-02T12:00:00Z"


def test_create_collection(fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests) -> None:
    collection_id = "test_collection"

    current_datetime = any_epoch_datetime_string()

    collection = create_collection(
        collection_id=collection_id,
        linz_slug=fake_linz_slug,
        collection_metadata=fake_collection_metadata,
        current_datetime=current_datetime,
        producers=[],
        licensors=[],
        stac_items=[],
        item_polygons=[],
        add_capture_dates=False,
        uri="test",
    )

    with subtests.test("collection ID"):
        assert collection.stac["id"] == collection_id

    with subtests.test("created datetime"):
        assert collection.stac["created"] == current_datetime

    with subtests.test("updated datetime"):
        assert collection.stac["updated"] == current_datetime


def test_create_collection_resupply(
    fake_collection_metadata: CollectionMetadata, fake_linz_slug: str, subtests: SubTests, tmp_path: Path
) -> None:
    collection_id = "test_collection"
    created_datetime = any_epoch_datetime()
    created_datetime_string = format_rfc_3339_datetime_string(created_datetime)
    existing_collection_content = {
        "type": "Collection",
        "stac_version": STAC_VERSION,
        "id": collection_id,
        "created": created_datetime_string,
        "updated": created_datetime_string,
    }
    existing_collection_path = tmp_path / "collection.json"
    existing_collection_path.write_text(json.dumps(existing_collection_content))

    updated_datetime_string = format_rfc_3339_datetime_string(created_datetime + timedelta(days=1))

    collection = create_collection(
        collection_id=collection_id,
        linz_slug=fake_linz_slug,
        collection_metadata=fake_collection_metadata,
        current_datetime=updated_datetime_string,
        producers=[],
        licensors=[],
        stac_items=[],
        item_polygons=[],
        add_capture_dates=False,
        uri="test",
        odr_url=tmp_path.as_posix(),
    )

    with subtests.test("created datetime"):
        assert collection.stac["created"] == existing_collection_content["created"]

    with subtests.test("updated datetime"):
        assert collection.stac["updated"] == updated_datetime_string


def test_create_item_with_odr_url(tmp_path: Path) -> None:
    item_name = "empty"
    existing_item_file = tmp_path / f"{item_name}.json"
    tiff_path = f"./scripts/tests/data/{item_name}.tiff"

    fake_gdal_info: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    item_from_scratch = create_item(
        tiff_path,
        "a start datetime",
        "an end datetime",
        item_name,
        "any GDAL version",
        "this current datetime",
        fake_gdal_info,
    )
    existing_item_file.write_text(json.dumps(item_from_scratch.stac))
    item_from_odr_unchanged = create_item(
        tiff_path,
        "a start datetime",
        "an end datetime",
        item_name,
        "any GDAL version",
        "this current datetime",
        fake_gdal_info,
        odr_url=tmp_path.as_posix(),
    )
    assert item_from_odr_unchanged.stac == item_from_scratch.stac

    item_from_odr_changed = create_item(
        tiff_path,
        "another start datetime",
        "another end datetime",
        item_name,
        "another GDAL version",
        "another current datetime",
        fake_gdal_info,
        odr_url=tmp_path.as_posix(),
    )
    del item_from_odr_changed.properties["start_datetime"]
    del item_from_odr_changed.properties["end_datetime"]
    del item_from_scratch.properties["start_datetime"]
    del item_from_scratch.properties["end_datetime"]
    assert item_from_odr_changed.stac == item_from_scratch.stac


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
        odr_url=tmp_path.as_posix(),
    )

    with subtests.test("created"):
        assert item.properties["created"] == current_datetime

    with subtests.test("updated"):
        assert item.properties["updated"] == current_datetime


def test_create_item_when_resupplying_with_changed_asset_file(subtests: SubTests, tmp_path: Path) -> None:
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
        odr_url=tmp_path.as_posix(),
    )

    with subtests.test(msg="assets.visual.created"):
        assert item.assets["visual"]["created"] == created_datetime

    with subtests.test(msg="assets.visual.updated"):
        assert item.assets["visual"]["updated"] == current_datetime
        assert item.assets["visual"]["updated"] == current_datetime
