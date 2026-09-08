from shapely.geometry import Polygon
from topo_imagery_common.geometry import BoundingBox, GeojsonPolygon
from topo_imagery_gdal.gdal.gdalinfo import GdalInfo


def get_extents(gdalinfo_result: GdalInfo) -> tuple[GeojsonPolygon, BoundingBox]:
    """Get the geometry and bounding box from the `gdalinfo`.

    Args:
        gdalinfo_result: a `gdalinfo` output

    Raises:
        Exception: if there is no `wgs84Extent` in the `gdalinfo`

    Returns:
        geometry and bbox
    """
    if gdalinfo_result["wgs84Extent"] is None:
        raise Exception("No WGS84 Extent was found")

    geometry = gdalinfo_result["wgs84Extent"]
    bbox = Polygon(geometry["coordinates"][0]).bounds

    return geometry, bbox
