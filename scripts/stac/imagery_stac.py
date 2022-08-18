
from typing import Any, Dict, List

from pystac import get_stac_version

from scripts.stac.util.stac_extensions import StacExtensions


def create_item(id: str, path: str, date: str, geometry: List[List[float]], bbox: List[float], checksum: str) -> Dict[str,Any]:
    return {
        "type": "Feature",
        "stac_version": get_stac_version(),
        "id": id,
        "properties": {
            "datetime": date,
        },
        "geometry": {"type": "Polygon", "coordinates": [geometry]},
        "bbox": bbox,
        "links": [
            {"rel": "self", "href": f"./{id}.json", "type": "application/json"},
        ],
        "assets": {"image": {"href": path, "type": "image/vnd.stac.geotiff", "file:checksum": checksum}},
        "stac_extensions": [StacExtensions.file.value],
    }

def validate_item() -> bool:
    # TODO: will implement in future PR
    return True

def create_collection() -> Dict[str, Any]:
    # TODO: will implement in future PR
    return {"":""}

def validate_collection() -> bool:
    # TODO: will implement in future PR
    return True
