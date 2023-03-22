import os
from typing import Any, Dict, Tuple

from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions


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
                    "href": os.path.join(".", os.path.basename(file)),
                    "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                    "file:checksum": checksum.multihash_as_hex(file),
                }
            },
            "stac_extensions": [StacExtensions.file.value],
        }

    def _get_properties(self) -> Dict[str, Any]:
        if not self.stac.get("properties"):
            self.stac["properties"] = {}
        properties: Dict[str, Any] = self.stac["properties"]
        return properties

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        properties = self._get_properties()
        properties["start_datetime"] = start_datetime
        properties["end_datetime"] = end_datetime
        properties["datetime"] = None

    # FIXME: redefine the 'Any'
    def update_spatial(self, geometry: Dict[str, Any], bbox: Tuple[float, ...]) -> None:
        self.stac["geometry"] = geometry
        self.stac["bbox"] = bbox

    def add_collection(self, collection_id: str) -> None:
        self.stac["collection"] = collection_id
        self.add_link(rel="collection")
        self.add_link(rel="parent")

    def add_link(self, rel: str, href: str = "./collection.json", file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})

    def add_stac_extension(self, link: str) -> None:
        """add a stac extension link in the 'stac_extensions' list if it does not already exist

        Args:
            link: to the extension json schema
        """
        if link not in self.stac["stac_extensions"]:
            self.stac["stac_extensions"].append(link)

    def add_eo_cloud_cover(self, cloud_percent: int) -> None:
        """add the cloud coverage to properties.'eo:cloud_cover'

        Args:
            cloud_percent: a number representing the estimated cloud coverage in %
        """
        properties = self._get_properties()
        properties["eo:cloud_cover"] = cloud_percent
