from datetime import datetime
from os import urandom
from typing import Callable

from shapely.geometry import Polygon
from topo_imagery_common.files.checksum import multihash_as_hex
from topo_imagery_common.geometry import GeojsonPolygon
from topo_imagery_stac.imagery.item import STACAsset, STACProcessing, STACProcessingSoftware


def fixed_now_function(now: datetime) -> Callable[[], datetime]:
    def func() -> datetime:
        return now

    return func


def any_stac_asset() -> STACAsset:
    return STACAsset(
        **{
            "href": "any href",
            "file:checksum": "any checksum",
            "created": "any created datetime",
            "updated": "any updated datetime",
        }
    )


def any_stac_processing() -> STACProcessing:
    return STACProcessing(
        **{
            "processing:datetime": "any processing datetime",
            "processing:software": STACProcessingSoftware(
                **{"gdal": "any GDAL version", "linz/topo-imagery": "any topo imagery version"}
            ),
            "processing:version": "any processing version",
        }
    )


def any_multihash_as_hex() -> str:
    return multihash_as_hex(urandom(64))


def any_geometry_and_bbox() -> tuple[GeojsonPolygon, tuple[float, ...]]:
    """A geometry and a matching bounding box, for tests that need spatial extents but do not assert on them."""
    geometry: GeojsonPolygon = {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}

    return geometry, Polygon(geometry["coordinates"][0]).bounds
