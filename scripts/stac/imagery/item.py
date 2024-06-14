import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files import fs
from scripts.files.fs import modified
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions

BoundingBox = tuple[float, float, float, float]


@dataclass
class Properties:
    created: str
    updated: str
    start_datetime: str
    end_datetime: str
    datetime: str | None = None


@dataclass
class ImageryItem:  # pylint: disable-msg=too-many-instance-attributes
    feature = "type"
    stac_version = STAC_VERSION
    id: str
    links: list[dict[str, str]]
    assets: dict[str, dict[str, str]]
    stac_extensions: list[str]
    properties: Properties
    geometry: dict[str, Any]
    bbox: BoundingBox
    collection_id: str

    def __init__(  # pylint: disable-msg=too-many-arguments
        self,
        id_: str,
        file: str,
        now: Callable[[], datetime],
        start_datetime: str,
        end_datetime: str,
        geometry: dict[str, Any],
        bbox: BoundingBox,
        collection_id: str,
    ) -> None:
        file_content = fs.read(file)
        file_modified_datetime = format_rfc_3339_datetime_string(modified(file))
        now_string = format_rfc_3339_datetime_string(now())
        self.id = id_

        self.links = [
            {"rel": "self", "href": f"./{id_}.json", "type": "application/json"},
            {"rel": "collection", "href": "./collection.json", "type": "application/json"},
            {"rel": "parent", "href": "./collection.json", "type": "application/json"},
        ]
        self.assets = {
            "visual": {
                "href": os.path.join(".", os.path.basename(file)),
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "file:checksum": checksum.multihash_as_hex(file_content),
                "created": file_modified_datetime,
                "updated": file_modified_datetime,
            }
        }
        self.stac_extensions = [StacExtensions.file.value]
        self.properties = Properties(
            created=now_string,
            updated=now_string,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        self.geometry = geometry
        self.bbox = bbox
        self.collection_id = collection_id
