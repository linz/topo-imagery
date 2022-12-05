from typing import Any, Dict, Optional

from linz_logger import get_log

from scripts.files.files_helper import get_file_name_from_path
from scripts.files.geotiff import get_extents
from scripts.gdal.gdalinfo import gdal_info, GdalInfo
from scripts.stac.imagery.item import ImageryItem


def create_item(
    file: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdalinfo_result: Optional[GdalInfo] = None,
) -> ImageryItem:
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file)
    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection_id)

    get_log().info("imagery stac item created", file=file)
    return item
