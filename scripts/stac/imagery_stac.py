from dataclasses import dataclass
from typing import Any, Dict, List

from pystac import get_stac_version

from scripts.stac.util.stac_extensions import StacExtensions


@dataclass
class ImageryItem:
    id: str
    path: str
    datetime: str
    geometry: List[List[float]]
    bbox: List[float]
    checksum: str


def create_item(item: ImageryItem) -> Dict[str, Any]:
    return {
        "type": "Feature",
        "stac_version": get_stac_version(),
        "id": item.id,
        "properties": {
            "datetime": item.datetime,
        },
        "geometry": {"type": "Polygon", "coordinates": [item.geometry]},
        "bbox": item.bbox,
        "links": [
            {"rel": "item", "href": f"./{item.id}.json", "type": "application/json"},
        ],
        "assets": {"image": {"href": item.path, "type": "image/vnd.stac.geotiff", "file:checksum": item.checksum}},
        "stac_extensions": [StacExtensions.file.value],
    }


def validate_stac() -> bool:
    # TODO: will implement in future PR
    return True


def create_collection() -> Dict[str, Any]:
    # TODO: will implement in future PR
    return {"": ""}


def validate_collection() -> bool:
    # TODO: will implement in future PR
    return True
