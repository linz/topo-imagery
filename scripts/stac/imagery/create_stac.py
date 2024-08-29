from typing import List, Optional

from linz_logger import get_log

from scripts.datetimes import utc_now
from scripts.files.files_helper import get_file_name_from_path
from scripts.files.geotiff import get_extents
from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.item import ImageryItem


def create_item(
    file: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdalinfo_result: GdalInfo | None = None,
    derived_from: Optional[List[str]] = [],  # FIXME
) -> ImageryItem:
    """Create an ImageryItem (STAC) to be linked to a Collection.

    Args:
        file: asset tiff file
        start_datetime: start date of the survey
        end_datetime: end date of the survey
        collection_id: collection id to link to the Item
        gdalinfo_result: result of the gdalinfo command. Defaults to None.

    Returns:
        a STAC Item wrapped in ImageryItem
    """
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file, utc_now)
    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection_id)

    for derived in derived_from:
        # TODO: add checksum and maybe created datetime and updated datetime
        item.add_link(rel="derived_from", href=derived)

    get_log().info("ImageryItem created", path=file)
    return item
