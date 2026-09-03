from decimal import Decimal
from typing import TypedDict

DECIMAL_DEGREES_1M = Decimal("0.00001")


class GeojsonPolygon(TypedDict):
    """A GeoJSON Polygon geometry. Other geometry types nest `coordinates` differently and are not covered by this type."""

    type: str
    """GeoJSON geometry type

    Always: "Polygon"
    """
    coordinates: list[list[list[float]]]
    """Linear rings of positions, the first being the exterior ring

    Example:
        [[[0, 1], [1, 1], [1, 0], [0, 0]]]
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
