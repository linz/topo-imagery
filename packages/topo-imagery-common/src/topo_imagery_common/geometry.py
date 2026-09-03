from decimal import Decimal

DECIMAL_DEGREES_1M = Decimal("0.00001")


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
