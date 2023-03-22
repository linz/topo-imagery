from typing import Optional

from linz_logger import get_log

from scripts.files.files_helper import get_file_name_from_path
from scripts.files.fs import read
from scripts.files.geotiff import get_extents
from scripts.gdal.gdalinfo import GdalInfo, gdal_info
from scripts.stac.imagery.import_metadata import MetadataType, get_cloud_percent
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.util.stac_extensions import StacExtensions


def create_item(
    file: str, start_datetime: str, end_datetime: str, collection_id: str, gdalinfo_result: Optional[GdalInfo] = None
) -> ImageryItem:
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file)
    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection_id)

    get_log().info("imagery stac item created", path=file)
    return item


def add_metadata(item: ImageryItem, metadata_file: str, metadata_type: MetadataType) -> None:
    """Modify STAC item to add external metadata.

    Args:
        item: The item that will be modified to add external metadata
        metadata_file: The path to the sidecar metadata file
        metadata_type: The type of the metadata
    """
    # Import sidecar metadata if specified
    if metadata_type == MetadataType.EARTHSCANNER:
        cloud_cover = get_cloud_percent(read(metadata_file).decode())
        if cloud_cover:
            item.add_stac_extension(StacExtensions.eo.value)
            item.add_eo_cloud_cover(cloud_cover)
    else:
        get_log().warn(f"unknown metadata type: {metadata_type}")
