import json
from decimal import Decimal
from typing import Any, Sequence

from linz_logger import get_log
from shapely import BufferCapStyle, BufferJoinStyle, to_geojson, union_all, wkt
from shapely.constructive import make_valid
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient

from scripts.logging.time_helper import time_in_ms

DECIMAL_DEGREES_1M = Decimal("0.00001")
"""
Degree precision of ~1m (decimal places 5, https://en.wikipedia.org/wiki/Decimal_degrees)
"""


def get_buffer_distance(gsd: Decimal) -> float:
    """The `gsd` (in meters) is multiplied by 2 and then by the 1m degree of precision.
    A `buffer factor` of 2 was decided on after experimenting with different outputs,
    details of this can be found in TDE-1049.

    Args:
        gsd: Ground Sample Distance in meters

    Returns:
        buffer distance as a float
    """
    return float(gsd * 2 * DECIMAL_DEGREES_1M)


def to_feature(geometry: BaseGeometry) -> dict[str, Any]:
    """Transform a BaseGeometry to a GeoJSON feature.

    Args:
        geometry: a BaseGeometry

    Returns:
        a GeoJSON document.
    """
    return {"geometry": json.loads(to_geojson(geometry)), "type": "Feature", "properties": {}}


def merge_polygons(polygons: Sequence[BaseGeometry], buffer_distance: float) -> BaseGeometry:
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
    union_rounded = wkt.loads(wkt.dumps(union_simplified, rounding_precision=8))
    # Ensure geometry is valid
    valid_geom = make_valid(union_rounded)
    # Apply right-hand rule winding order (exterior rings should be counter-clockwise) to the geometry
    # Ref: https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.6
    oriented_valid_geom = orient(valid_geom, sign=1.0)

    return oriented_valid_geom


def generate_capture_area(polygons: Sequence[BaseGeometry], gsd: Decimal) -> dict[str, Any]:
    """Generate the capture area from a list of BaseGeometries.
    Providing the `gsd` allows to round the geometry as we've seen some tiffs
    geometry being slightly off, sometimes due to rounding issue in their
    creation process (before delivery).
    If we don't apply this rounding, we could get a very small gaps between tiffs
    which would result in a capture area having gaps.

    Note that all the polygons are buffered which means a gap bigger than the gsd,
    but < buffer_factor*2 will be closed.

    Args:
        polygons: list of BaseGeometries of the area
        gsd: Ground Sample Distance in meters

    Returns:
        The capture-area geojson document.
    """
    start_time = time_in_ms()
    get_log().trace("Generating capture-area started")

    merged_polygons = merge_polygons(polygons, get_buffer_distance(gsd))

    get_log().trace(
        "Generating capture-area ended",
        duration=time_in_ms() - start_time,
    )

    return to_feature(merged_polygons)
