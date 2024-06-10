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


@dataclass
class ImageryItem:
    stac: dict[str, Any]

    def __init__(  # pylint: disable-msg=too-many-arguments
        self,
        id_: str,
        file: str,
        now: Callable[[], datetime],
        start_datetime: str,
        end_datetime: str,
        geometry: dict[str, Any],
        bbox: tuple[float, ...],
        collection_id: str,
    ) -> None:
        file_content = fs.read(file)
        file_modified_datetime = format_rfc_3339_datetime_string(modified(file))
        now_string = format_rfc_3339_datetime_string(now())
        self.stac = {
            "type": "Feature",
            "stac_version": STAC_VERSION,
            "id": id_,
            "links": [
                {"rel": "self", "href": f"./{id_}.json", "type": "application/json"},
                {"rel": "collection", "href": "./collection.json", "type": "application/json"},
                {"rel": "parent", "href": "./collection.json", "type": "application/json"},
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
            "properties": {
                "created": now_string,
                "updated": now_string,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "datetime": None,
            },
            "geometry": geometry,
            "bbox": bbox,
            "collection": collection_id,
        }
