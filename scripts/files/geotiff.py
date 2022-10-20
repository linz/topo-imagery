from typing import Any, Dict, List, Tuple

from shapely.geometry import Polygon


def get_extents(gdalinfo_result: Dict[Any, Any]) -> Tuple[List[List[float]], List[float]]:

    geometry = gdalinfo_result["wgs84Extent"]["coordinates"][0]
    bbox = list(Polygon(geometry).bounds)

    return geometry, bbox
