import json
from typing import Any, Dict, List

from shapely import BufferCapStyle, BufferJoinStyle, Geometry, to_geojson, union_all
from shapely.geometry import Polygon


def merge_polygons(polygons: List[Polygon], buffer_distance: float) -> Geometry:
    """Merge a list of polygons by converting them to a single geometry that covers the same area.
    A buffer distance is used to buffer out the polygons before dissolving them together and then negative buffer them back in.
    The merged geometry is simplify (rounded) to the decimal used for the buffer.

    Args
    ----
        polygons: list of polygons to merge
        buffer_distance: decimal places to use to buffer the polygons

    Returns:
        A single Geometry.
    """
    buffered_polygons = []
    for poly in polygons:
        # Buffer each polygon to round up to the `buffer_distance`
        buffered_poly = poly.buffer(buffer_distance, cap_style=BufferCapStyle.flat, join_style=BufferJoinStyle.mitre)
        buffered_polygons.append(buffered_poly)
    union = union_all(buffered_polygons)
    # Negative buffer back in the polygons
    union = union.buffer(-buffer_distance, cap_style=BufferCapStyle.flat, join_style=BufferJoinStyle.mitre)
    union = union.simplify(buffer_distance)

    return union


def generate_capture_area(polygons: List[Polygon]) -> Dict[str, Any]:
    """Generate the capture area from a list of polygons.

    Args:
        polygons: list of polygons of the area

    Returns:
        The capture-area document.
    """
    # Degree precision of 1mm (decimal places 8, https://en.wikipedia.org/wiki/Decimal_degrees)
    # It allows to round the geometry as we've seen some tiffs geometry being slightly off by less than 1mm,
    # due to rounding issue in their creation process (before delivery).
    # If we don't apply this rounding, we could get a very small gap between tiffs
    # which would result in a capture area not being a single polygon.
    buffer_distance = 0.0000001
    merged_polygons = merge_polygons(polygons, buffer_distance)

    return {"geometry": json.loads(to_geojson(merged_polygons)), "type": "Feature", "properties": {}}
