from typing import Any, Dict, List, Tuple

from shapely.geometry import Polygon


def get_extents(gdalinfo_result: Dict[Any, Any]) -> Tuple[List[List[float]], List[float]]:

    geometry = gdalinfo_result["wgs84Extent"]
    bbox = Polygon(geometry["coordinates"][0]).bounds

    return geometry, bbox
