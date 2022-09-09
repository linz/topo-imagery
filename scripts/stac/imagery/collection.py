from typing import Any, Dict, Optional

import ulid

PYSTAC_VERSION = "1.0.0"


class ImageryCollection:
    stac: Dict[str, Any]

    def __init__(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        self.stac = {
            "type": "Collection",
            "stac_version": PYSTAC_VERSION,
            "id": str(ulid.ULID()),
            "title": title,
            "description": description,
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
        }
