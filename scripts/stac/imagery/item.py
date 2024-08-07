import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files import fs
from scripts.files.fs import modified
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions


class ImageryItem:
    stac: dict[str, Any]

    def __init__(self, id_: str, file: str, now: Callable[[], datetime]) -> None:
        file_content = fs.read(file)
        file_modified_datetime = format_rfc_3339_datetime_string(modified(file))
        now_string = format_rfc_3339_datetime_string(now())
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
                    "file:checksum": checksum.multihash_as_hex(file_content),
                    "created": file_modified_datetime,
                    "updated": file_modified_datetime,
                }
            },
            "stac_extensions": [StacExtensions.file.value],
            "properties": {"created": now_string, "updated": now_string},
        }

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        """Update the Item `start_datetime` and `end_datetime` property.

        Args:
            start_datetime: a start date in `YYYY-MM-DD` format
            end_datetime: a end date in `YYYY-MM-DD` format
        """
        self.stac.setdefault("properties", {})
        self.stac["properties"]["start_datetime"] = start_datetime
        self.stac["properties"]["end_datetime"] = end_datetime
        self.stac["properties"]["datetime"] = None

    # FIXME: redefine the 'Any'
    def update_spatial(self, geometry: dict[str, Any], bbox: tuple[float, ...]) -> None:
        """Update the `geometry` and `bbox` (bounding box) of the Item.

        Args:
            geometry: a geometry
            bbox: a bounding box
        """
        self.stac["geometry"] = geometry
        self.stac["bbox"] = bbox

    def add_collection(self, collection_id: str) -> None:
        """Link a Collection to the Item as its `collection` and `parent`.

        Args:
            collection_id: the id of the collection to link
        """
        self.stac["collection"] = collection_id
        self.add_link(rel="collection")
        self.add_link(rel="parent")

    def add_link(self, rel: str, href: str = "./collection.json", file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})
