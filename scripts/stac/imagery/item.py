import os
from collections.abc import Callable
from datetime import datetime
from os import environ
from typing import Any

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files import fs
from scripts.files.fs import modified
from scripts.stac.link import Link, Relation
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.media_type import StacMediaType
from scripts.stac.util.stac_extensions import StacExtensions


class ImageryItem:
    stac: dict[str, Any]

    def __init__(self, id_: str, file: str, gdal_version: str, now: Callable[[], datetime]) -> None:
        file_content = fs.read(file)
        file_modified_datetime = format_rfc_3339_datetime_string(modified(file))
        now_string = format_rfc_3339_datetime_string(now())
        if (topo_imagery_hash := environ.get("GIT_HASH")) is not None:
            commit_url = f"https://github.com/linz/topo-imagery/commit/{topo_imagery_hash}"
        else:
            commit_url = "GIT_HASH not specified"

        self.stac = {
            "type": "Feature",
            "stac_version": STAC_VERSION,
            "id": id_,
            "links": [Link(path=f"./{id_}.json", rel=Relation.SELF, media_type=StacMediaType.GEOJSON).stac],
            "assets": {
                "visual": {
                    "href": os.path.join(".", os.path.basename(file)),
                    "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                    "file:checksum": checksum.multihash_as_hex(file_content),
                    "created": file_modified_datetime,
                    "updated": file_modified_datetime,
                }
            },
            "stac_extensions": [StacExtensions.file.value, StacExtensions.processing.value],
            "properties": {
                "created": now_string,
                "updated": now_string,
                "processing:datetime": now_string,
                "processing:software": {"gdal": gdal_version, "linz/topo-imagery": commit_url},
                "processing:version": environ.get("GIT_VERSION", "GIT_VERSION not specified"),
            },
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
        self.add_link(Link(path="./collection.json", rel=Relation.COLLECTION, media_type=StacMediaType.JSON))
        self.add_link(Link(path="./collection.json", rel=Relation.PARENT, media_type=StacMediaType.JSON))

    def add_link(self, link: Link) -> None:
        self.stac["links"].append(link.stac)
