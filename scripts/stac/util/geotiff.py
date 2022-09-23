from typing import List, Tuple

from scripts.gdal.gdalinfo import gdal_info


def get_extents(path: str) -> Tuple[List[List[float]], List[float]]:
    corner_coordinates = gdal_info(path)["cornerCoordinates"]

    upper_left = [corner_coordinates["upperLeft"][0], corner_coordinates["upperLeft"][1]]
    upper_right = [corner_coordinates["upperRight"][0], corner_coordinates["upperRight"][1]]
    lower_left = [corner_coordinates["lowerLeft"][0], corner_coordinates["lowerLeft"][1]]
    lower_right = [corner_coordinates["lowerRight"][0], corner_coordinates["lowerRight"][1]]

    geometry = [upper_left, upper_right, lower_right, lower_left]
    bbox = [upper_left[0], upper_left[1], lower_right[0], lower_right[1]]
    return geometry, bbox
