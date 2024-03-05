import json
from typing import Any, Dict, List

from shapely import BufferCapStyle, BufferJoinStyle, Geometry, to_geojson, union_all
from shapely.geometry import Polygon

DECIMAL_DEGREES_1M = 0.00001
"""
Degree precision of ~1m (decimal places 5, https://en.wikipedia.org/wiki/Decimal_degrees)
"""


def gsd_to_float(gsd: str) -> float:
    """Transform the gsd from its string/human readable format to a float.

    Args:
        gsd: gsd as it's passed to the cli

    Returns:
        gsd as a float

    Examples:
        >>> gsd_to_float("0.2m")
        0.2
    """
    return float(gsd.replace("m", ""))


def get_buffer_distance(gsd: float) -> float:
    """The `gsd` (in meters) is multiplied by 2 and then by the 1m degree of precision.
    A `buffer factor` of 2 was decided on after experimenting with different outputs,
    details of this can be found in TDE-1049.

    Args:
        gsd: Ground Sample Distance in meters

    Returns:
        buffer distance as a float
    """
    return gsd * 2 * DECIMAL_DEGREES_1M


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
    Providing the `gsd` allows to round the geometry as we've seen some tiffs
    geometry being slightly off, sometimes due to rounding issue in their
    creation process (before delivery).
    If we don't apply this rounding, we could get a very small gaps between tiffs
    which would result in a capture area having gaps.

    Note that all the polygons are buffered which means a gap bigger than the gsd,
    but < buffer_factor*2 will be closed.

    Args:
        polygons: list of polygons of the area
        gsd: Ground Sample Distance in meters

    Returns:
        The capture-area geojson document.
    """
    merged_polygons = merge_polygons(polygons, get_buffer_distance(gsd))

    return to_feature(merged_polygons)
