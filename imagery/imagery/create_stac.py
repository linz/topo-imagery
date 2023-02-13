from typing import Optional

from linz_logger import get_log

from common.files.files_helper import get_file_name_from_path
from common.files.geotiff import get_extents
from imagery.gdal.gdalinfo import GdalInfo, gdal_info
from common.stac.imagery.item import ImageryItem


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

    get_log().info("imagery stac item created", path=file)
    return item
