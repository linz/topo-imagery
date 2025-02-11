import json
import os
from typing import Any, TypeAlias

from linz_logger import get_log
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from scripts.files import fs
from scripts.files.files_helper import ContentType, get_file_name_from_path
from scripts.files.fs import NoSuchFileError, read, write
from scripts.files.geotiff import get_extents
from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.item import ImageryItem, STACAsset, STACProcessing, STACProcessingSoftware
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.link import Link, Relation
from scripts.stac.util import checksum
from scripts.stac.util.media_type import StacMediaType

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
JSON_Dict: TypeAlias = dict[str, "JSON"]


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def create_collection(
    collection_id: str,
    linz_slug: str,
    collection_metadata: CollectionMetadata,
    current_datetime: str,
    producers: list[str],
    licensors: list[str],
    stac_items: list[dict[Any, Any]],
    item_polygons: list[BaseGeometry],
    add_capture_dates: bool,
    uri: str,
    add_title_suffix: bool = False,
    odr_url: str | None = None,
) -> ImageryCollection:
    """Create an ImageryCollection object.
    If `item_polygons` is not empty, it will add a generated capture area to the collection.

    Args:
        collection_id: id of the collection
        linz_slug: the linz:slug attribute for this collection
        collection_metadata: metadata of the collection
        current_datetime: datetime string that represents the current time when the item is created.
        producers: producers of the dataset
        licensors: licensors of the dataset
        stac_items: items to link to the collection
        item_polygons: polygons of the items linked to the collection
        add_capture_dates: whether to add a capture-dates.geojson.gz file to the collection assets
        uri: path of the dataset
        add_title_suffix: whether to add a title suffix to the collection title based on the lifecycle
        odr_url: path of the published dataset. Defaults to None.

    Returns:
        an ImageryCollection object
    """
    if odr_url:
        collection = ImageryCollection.from_file(
            os.path.join(odr_url, "collection.json"), collection_metadata, current_datetime
        )

    else:
        collection = ImageryCollection(
            metadata=collection_metadata,
            created_datetime=current_datetime,
            updated_datetime=current_datetime,
            linz_slug=linz_slug,
            collection_id=collection_id,
            providers=get_providers(licensors, producers),
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


def get_providers(licensors: list[str], producers: list[str]) -> list[Provider]:
    providers: list[Provider] = []
    for producer_name in producers:
        providers.append({"name": producer_name, "roles": [ProviderRole.PRODUCER]})
    for licensor_name in licensors:
        providers.append({"name": licensor_name, "roles": [ProviderRole.LICENSOR]})
    return providers


def create_item(
    asset_path: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdal_version: str,
    current_datetime: str,
    gdalinfo_result: GdalInfo | None = None,
    derived_from: list[str] | None = None,
    odr_url: str | None = None,
) -> ImageryItem:
    """Create an ImageryItem (STAC) to be linked to a Collection.

    Args:
        asset_path: path of the visual asset (TIFF)
        start_datetime: start date of the survey
        end_datetime: end date of the survey
        collection_id: collection id to link to the Item
        gdal_version: GDAL version
        current_datetime: date and time for setting consistent update and/or creation timestamp
        gdalinfo_result: result of the gdalinfo command. Defaults to None.
        derived_from: list of STAC Items from where this Item is derived. Defaults to None.
        odr_url: S3 URL of the already published files in ODR (if this is a resupply). Defaults to None.

    Returns:
        a STAC Item wrapped in ImageryItem
    """
    item = create_or_load_base_item(asset_path, gdal_version, current_datetime, odr_url)
    base_stac = item.stac.copy()

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(asset_path)

    if item.stac.get("links") is not None:
        # Remove existing derived_from links in case of resupply
        item.stac["links"] = [link for link in item.stac["links"] if link["rel"] != "derived_from"]

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

    if item.stac != base_stac and item.stac["properties"]["updated"] != current_datetime:
        item.stac["properties"][
            "updated"
        ] = current_datetime  # some of the metadata has changed, so we need to make sure the `updated` time is set correctly

    get_log().info("ImageryItem created", path=asset_path)
    return item


def create_or_load_base_item(
    asset_path: str, gdal_version: str, current_datetime: str, odr_url: str | None = None
) -> ImageryItem:
    """
    Args:
        asset_path: path with filename of the visual asset (TIFF)
        gdal_version: GDAL version string
        current_datetime: date and time used for setting consistent update and/or creation timestamp
        odr_url: S3 URL of the already published files in ODR (if this is a resupply). Defaults to None.

    Returns:
        An ImageryItem with basic information.
    """
    id_ = get_file_name_from_path(asset_path)
    file_content = fs.read(asset_path)
    file_content_checksum = checksum.multihash_as_hex(file_content)

    if (topo_imagery_hash := os.environ.get("GIT_HASH")) is not None:
        commit_url = f"https://github.com/linz/topo-imagery/commit/{topo_imagery_hash}"
    else:
        commit_url = "GIT_HASH not specified"

    stac_processing = STACProcessing(
        **{
            "processing:datetime": current_datetime,
            "processing:software": STACProcessingSoftware(**{"gdal": gdal_version, "linz/topo-imagery": commit_url}),
            "processing:version": os.environ.get("GIT_VERSION", "GIT_VERSION not specified"),
        }
    )

    if odr_url:
        try:
            imagery_item = ImageryItem.from_file(os.path.join(odr_url, f"{id_}.json"))
            imagery_item.update_checksum_related_metadata(file_content_checksum, stac_processing_data=stac_processing)
            return imagery_item

        except NoSuchFileError:
            get_log().info(f"No Item is published for ID: {id_}")

    stac_asset = STACAsset(
        **{
            "href": os.path.join(".", os.path.basename(asset_path)),
            "file:checksum": file_content_checksum,
            "created": current_datetime,
            "updated": current_datetime,
        }
    )

    return ImageryItem(id_, stac_asset, stac_processing)
