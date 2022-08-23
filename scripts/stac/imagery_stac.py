from typing import Any, Dict

from scripts.stac.util import checksum, geotiff
from scripts.stac.util.stac_extensions import StacExtensions

PYSTAC_VERSION = "1.0.0"


def create_imagery_stac_item(id_: str, path: str, start_datetime: str, end_datetime: str) -> Dict[str, Any]:
    geometry, bbox = geotiff.get_extents(path)
    return {
        "type": "Feature",
        "stac_version": PYSTAC_VERSION,
        "id": id_,
        "properties": {
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "datetime": None,
        },
        "geometry": {"type": "Polygon", "coordinates": [geometry]},
        "bbox": bbox,
        "links": [
            {"rel": "self", "href": f"./{id_}.json", "type": "application/json"},
        ],
        "assets": {
            "image": {
                "href": path,
                "type": "image/tiff; application:geotiff; profile:cloud-optimized",
                "file:checksum": checksum.multihash_as_hex(path),
            }
        },
        "stac_extensions": [StacExtensions.file.value],
    }
