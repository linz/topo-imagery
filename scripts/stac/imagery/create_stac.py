import json
import os
from typing import Any

from linz_logger import get_log
from shapely.geometry.base import BaseGeometry

from scripts.datetimes import format_rfc_3339_datetime_string, utc_now
from scripts.files import fs
from scripts.files.files_helper import get_file_name_from_path
from scripts.files.fs import modified, read
from scripts.files.geotiff import get_extents
from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem, STACAsset, STACProcessing, STACProcessingSoftware
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.link import Link, Relation
from scripts.stac.util import checksum
from scripts.stac.util.media_type import StacMediaType


# pylint: disable=too-many-arguments
def create_collection(
    collection_id: str,
    linz_slug: str,
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
        linz_slug: the linz:slug attribute for this collection
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
        linz_slug=linz_slug,
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


def create_item(
    asset_path: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdal_version: str,
    gdalinfo_result: GdalInfo | None = None,
    derived_from: list[str] | None = None,
) -> ImageryItem:
    """Create an ImageryItem (STAC) to be linked to a Collection.

    Args:
        asset_path: path of the visual asset (TIFF)
        start_datetime: start date of the survey
        end_datetime: end date of the survey
        collection_id: collection id to link to the Item
        gdal_version: GDAL version
        gdalinfo_result: result of the gdalinfo command. Defaults to None.
        derived_from: list of STAC Items from where this Item is derived. Defaults to None.

    Returns:
        a STAC Item wrapped in ImageryItem
    """
    item = create_base_item(asset_path, gdal_version)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(asset_path)

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


def create_base_item(asset_path: str, gdal_version: str) -> ImageryItem:
    """
    Args:
        asset_path: path of the visual asset (TIFF)
        gdal_version: GDAL version string

    Returns:
        An ImageryItem with basic information.
    """
    id_ = get_file_name_from_path(asset_path)
    file_content = fs.read(asset_path)
    file_content_checksum = checksum.multihash_as_hex(file_content)
    file_modified_datetime = format_rfc_3339_datetime_string(modified(asset_path))
    now_string = format_rfc_3339_datetime_string(utc_now())

    if (topo_imagery_hash := os.environ.get("GIT_HASH")) is not None:
        commit_url = f"https://github.com/linz/topo-imagery/commit/{topo_imagery_hash}"
    else:
        commit_url = "GIT_HASH not specified"

    stac_processing = STACProcessing(
        **{
            "processing:datetime": now_string,
            "processing:software": STACProcessingSoftware(**{"gdal": gdal_version, "linz/topo-imagery": commit_url}),
            "processing:version": os.environ.get("GIT_VERSION", "GIT_VERSION not specified"),
        }
    )

    stac_asset = STACAsset(
        **{
            "href": os.path.join(".", os.path.basename(asset_path)),
            "file:checksum": file_content_checksum,
            "created": file_modified_datetime,
            "updated": file_modified_datetime,
        }
    )

    return ImageryItem(id_, now_string, stac_asset, stac_processing)
