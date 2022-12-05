from typing import Any, Dict, List, Tuple
from scripts.gdal.gdalinfo import GdalInfo

from shapely.geometry import Polygon


def get_extents(gdalinfo_result: GdalInfo) -> Tuple[Dict[str, List[float]], List[float]]:
    if gdalinfo_result["wgs84Extent"] is None:
        raise Exception("No WGS84 Extent was found")

    geometry = gdalinfo_result["wgs84Extent"]
    bbox = Polygon(geometry["coordinates"][0]).bounds

    return geometry, bbox
