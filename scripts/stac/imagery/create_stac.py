import json
from os import path
from typing import Any, cast

from linz_logger import get_log
from shapely.geometry.base import BaseGeometry

from scripts.datetimes import format_rfc_3339_datetime_string, utc_now
from scripts.files.files_helper import get_file_name_from_path
from scripts.files.fs import NoSuchFileError, modified, read
from scripts.files.geotiff import get_extents
from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem, STACAsset
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.link import Link, Relation
from scripts.stac.util.checksum import multihash_as_hex
from scripts.stac.util.media_type import StacMediaType


# pylint: disable=too-many-arguments
def create_collection(
    collection_id: str,
    collection_metadata: CollectionMetadata,
    producers: list[str],
    licensors: list[str],
    stac_items: list[dict[Any, Any]],
    item_polygons: list[BaseGeometry],
    add_capture_dates: bool,
    uri: str,
    add_title_suffix: bool = False,
) -> ImageryCollection:
    """Create an ImageryCollection object.
    If `item_polygons` is not empty, it will add a generated capture area to the collection.

    Args:
        collection_id: id of the collection
        collection_metadata: metadata of the collection
        producers: producers of the dataset
        licensors: licensors of the dataset
        stac_items: items to link to the collection
        item_polygons: polygons of the items linked to the collection
        add_capture_dates: whether to add a capture-dates.geojson.gz file to the collection assets
        uri: path of the dataset
        add_title_suffix: whether to add a title suffix to the collection title based on the lifecycle

    Returns:
        an ImageryCollection object
    """
    providers: list[Provider] = []
    for producer_name in producers:
        providers.append({"name": producer_name, "roles": [ProviderRole.PRODUCER]})
    for licensor_name in licensors:
        providers.append({"name": licensor_name, "roles": [ProviderRole.LICENSOR]})

    collection = ImageryCollection(
        metadata=collection_metadata,
        now=utc_now,
        collection_id=collection_id,
        providers=providers,
        add_title_suffix=add_title_suffix,
    )

    for item in stac_items:
        collection.add_item(item)

    if add_capture_dates:
        collection.add_capture_dates(uri)

    if item_polygons:
        collection.add_capture_area(item_polygons, uri)
        get_log().info(
            "Capture area created",
        )

    return collection


def get_item_created_datetime(existing_item: dict[str, Any], current_datetime: str) -> str:
    return cast(str, existing_item.get("properties", {}).get("created", current_datetime))


def create_item(
    asset_path: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    current_datetime: str,
    gdalinfo_result: GdalInfo | None = None,
    derived_from: list[str] | None = None,
    published_path: str | None = None,
) -> ImageryItem:
    """Create an ImageryItem (STAC) to be linked to a Collection.

    Args:
        asset_path: asset tiff file
        start_datetime: start date of the survey
        end_datetime: end date of the survey
        collection_id: collection id to link to the Item
        current_datetime: datetime string that represents the current time when the item is created.
        gdalinfo_result: result of the gdalinfo command. Defaults to None.
        derived_from: list of STAC Items from where this Item is derived. Defaults to None.
        published_path: path of the published dataset. Defaults to None.

    Returns:
        a STAC Item wrapped in ImageryItem
    """
    item_id = get_file_name_from_path(asset_path)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(asset_path)

    existing_item = {}
    if published_path:
        try:
            existing_item = json.loads(read(path.join(published_path, f"{item_id}.json")).decode("UTF-8"))
        except NoSuchFileError:
            get_log().info(f"No Item is published for ID: {item_id}")

    item = ImageryItem(
        item_id,
        get_stac_asset(item_id, asset_path, existing_item),
        get_item_created_datetime(existing_item, current_datetime),
        current_datetime,
    )

    if derived_from is not None:
        for derived in derived_from:
            derived_item_content = read(derived)
            derived_stac = json.loads(derived_item_content.decode("UTF-8"))
            if not start_datetime or derived_stac["properties"]["start_datetime"] < start_datetime:
                start_datetime = derived_stac["properties"]["start_datetime"]
            if not end_datetime or derived_stac["properties"]["end_datetime"] > end_datetime:
                end_datetime = derived_stac["properties"]["end_datetime"]
            item.add_link(
                Link(
                    path=derived,
                    rel=Relation.DERIVED_FROM,
                    media_type=StacMediaType.GEOJSON,
                    file_content=derived_item_content,
                )
            )

    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(*get_extents(gdalinfo_result))
    item.add_collection(collection_id)

    get_log().info("ImageryItem created", path=asset_path)
    return item


def get_stac_asset(item_id: str, asset_path: str, existing_item: dict[str, Any]) -> STACAsset:
    """Make a STAC Asset object.

    Args:
        item_id: ID of the STAC Item
        asset_path: Path of the visual asset file
        existing_item: STAC object of the existing Item

    Returns:
        a STAC Asset object
    """
    file_content = read(asset_path)
    multihash = multihash_as_hex(file_content)

    file_created_datetime = file_updated_datetime = format_rfc_3339_datetime_string(modified(asset_path))

    try:
        file_created_datetime = existing_item["assets"]["visual"]["created"]
    except KeyError:
        get_log().info(f"Existing Item for {item_id} does not have 'assets.visual.created' attribute")

    try:
        if multihash == existing_item["assets"]["visual"]["file:checksum"]:
            file_updated_datetime = existing_item["assets"]["visual"]["updated"]
    except KeyError:
        get_log().info(f"Existing Item for {item_id} does not have 'assets.visual' attributes")

    return STACAsset(
        **{
            "href": asset_path,
            "file:checksum": multihash,
            "created": file_created_datetime,
            "updated": file_updated_datetime,
        }
    )
