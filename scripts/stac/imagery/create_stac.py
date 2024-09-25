import json

from linz_logger import get_log

from scripts.datetimes import utc_now
from scripts.files.files_helper import get_file_name_from_path
from scripts.files.fs import read
from scripts.files.geotiff import get_extents
from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo
from scripts.stac.imagery.item import ImageryItem
from scripts.stac.link import Link, Relation
from scripts.stac.util.media_type import StacMediaType


def create_item(
    file: str,
    start_datetime: str,
    end_datetime: str,
    collection_id: str,
    gdalinfo_result: GdalInfo | None = None,
    derived_from: list[str] | None = None,
) -> ImageryItem:
    """Create an ImageryItem (STAC) to be linked to a Collection.

    Args:
        file: asset tiff file
        start_datetime: start date of the survey
        end_datetime: end date of the survey
        collection_id: collection id to link to the Item
        gdalinfo_result: result of the gdalinfo command. Defaults to None.
        derived_from: list of STAC Items from where this Item is derived. Defaults to None.

    Returns:
        a STAC Item wrapped in ImageryItem
    """
    id_ = get_file_name_from_path(file)

    if not gdalinfo_result:
        gdalinfo_result = gdal_info(file)

    geometry, bbox = get_extents(gdalinfo_result)

    item = ImageryItem(id_, file, utc_now)

    if derived_from is not None:
        for derived in derived_from:
            derived_item_content = read(derived)
            derived_stac = json.loads(derived_item_content.decode("UTF-8"))
            if not start_datetime and not end_datetime:
                start_datetime = derived_stac["properties"]["start_datetime"]
                end_datetime = derived_stac["properties"]["end_datetime"]
            else:
                start_datetime = min(start_datetime, derived_stac["properties"]["start_datetime"])
                end_datetime = max(end_datetime, derived_stac["properties"]["end_datetime"])
            item.add_link(
                Link(
                    path=derived,
                    rel=Relation.DERIVED_FROM,
                    media_type=StacMediaType.GEOJSON,
                    file_content=derived_item_content,
                )
            )

    item.update_datetime(start_datetime, end_datetime)
    item.update_spatial(geometry, bbox)
    item.add_collection(collection_id)

    get_log().info("ImageryItem created", path=file)
    return item
