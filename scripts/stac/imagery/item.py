from typing import TYPE_CHECKING, Any, Dict, List

from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions

if TYPE_CHECKING:
    from scripts.stac.imagery.collection import ImageryCollection


class ImageryItem:
    stac: Dict[str, Any]

    def __init__(self, id_: str, file: str) -> None:
        self.stac = {
            "type": "Feature",
            "stac_version": STAC_VERSION,
            "id": id_,
            "links": [
                {"rel": "self", "href": f"./{id_}.json", "type": "application/json"},
            ],
            "assets": {
                "visual": {
                    "href": file,
                    "type": "image/tiff; application:geotiff; profile:cloud-optimized",
                    "file:checksum": checksum.multihash_as_hex(file),
                }
            },
            "stac_extensions": [StacExtensions.file.value],
        }

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        self.stac["properties"] = {
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "datetime": None,
        }

    def update_spatial(self, geometry: List[List[float]], bbox: List[float]) -> None:
        self.stac["geometry"] = {"type": "Polygon", "coordinates": [geometry]}
        self.stac["bbox"] = bbox

    def add_collection(self, collection: "ImageryCollection") -> None:
        self.stac["collection"] = collection.stac["id"]
        self.add_link(rel="collection")
        self.add_link(rel="parent")

    def add_link(self, rel: str, href: str = "./collection.json", file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})
