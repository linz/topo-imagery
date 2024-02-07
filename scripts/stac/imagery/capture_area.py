import json
from typing import Any, Dict, List

from shapely import BufferCapStyle, BufferJoinStyle, Geometry, to_geojson, union_all
from shapely.geometry import Polygon

DECIMAL_DEGREES_1M = 0.00001
"""
Degree precision of ~1m (decimal places 5, https://en.wikipedia.org/wiki/Decimal_degrees)
"""


def to_feature(geometry: Geometry) -> Dict[str, Any]:
    """Transform a Geometry to a GeoJSON feature.

    Args:
        geometry: a Geometry

    Returns:
        a GeoJSON document.
    """
    return {"geometry": json.loads(to_geojson(geometry)), "type": "Feature", "properties": {}}


def merge_polygons(polygons: List[Polygon], buffer_distance: float) -> Geometry:
    """Merge a list of polygons by converting them to a single geometry that covers the same area.
    A buffer distance is used to buffer out the polygons before dissolving them together and then negative buffer them back in.
    The merged geometry is simplify (rounded) to the decimal used for the buffer.

    Args:
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
    union_buffered = union_all(buffered_polygons)
    # Negative buffer back in the polygons
    union_unbuffered = union_buffered.buffer(-buffer_distance, cap_style=BufferCapStyle.flat, join_style=BufferJoinStyle.mitre)
    union_simplified = union_unbuffered.simplify(buffer_distance)

    return union_simplified


def generate_capture_area(polygons: List[Polygon], gsd: float) -> Dict[str, Any]:
    """Generate the capture area from a list of polygons.

    Args:
        polygons: list of polygons of the area
        gsd: Ground Sample Distance in meter

    Returns:
        The capture-area geojson document.
    """
    # It allows to round the geometry as we've seen some tiffs geometry being slightly off,
    # sometimes due to rounding issue in their creation process (before delivery).
    # If we don't apply this rounding, we could get a very small gaps between tiffs
    # which would result in a capture area having gaps.
    # We multiply the gsd (in meter) to the 1m degree of precision.
    # Note that all the polygons are buffered which means a gap bigger than the gsd,
    # but < gsd*2) will be closed.
    buffer_distance = DECIMAL_DEGREES_1M * gsd
    merged_polygons = merge_polygons(polygons, buffer_distance)

    return to_feature(merged_polygons)
