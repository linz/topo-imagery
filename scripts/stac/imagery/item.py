import json
from typing import Any, Dict, List, Optional

from scripts.files.fs import read
from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions


class ImageryItem:
    stac: Dict[str, Any]
    path: str

    def __init__(self, id_: Optional[str] = None, path: Optional[str] = None) -> None:
        if path and not id_:
            self.stac = json.loads(read(path))
            self.path = path
        elif id_ and path:
            self.stac = {
                "type": "Feature",
                "stac_version": STAC_VERSION,
                "id": id_,
                "links": [
                    {"rel": "self", "href": f"./{id_}.json", "type": "application/json"},
                ],
                "assets": {
                    "visual": {
                        "href": path,
                        "type": "image/tiff; application:geotiff; profile:cloud-optimized",
                        "file:checksum": checksum.multihash_as_hex(path),
                    }
                },
                "stac_extensions": [StacExtensions.file.value],
            }
        else:
            raise Exception("incorrect initialising parameters must have 'path' or 'id_ and path'")

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        self.stac["properties"] = {
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "datetime": None,
        }

    def update_spatial(self, geometry: List[List[float]], bbox: List[float]) -> None:
        self.stac["geometry"] = {"type": "Polygon", "coordinates": [geometry]}
        self.stac["bbox"] = bbox

    def add_collection(self, collection: ImageryCollection) -> None:
        self.stac["collection"] = collection.stac["title"]
        if collection.path:
            self.add_link(rel="collection", href=collection.path)
            self.add_link(rel="parent", href=collection.path)

    def add_link(self, rel: str, href: str, file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})
