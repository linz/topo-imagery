from typing import Any, Dict, List, Optional

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

    def add_link(self, href: str, rel: str = "item", file_type: str = "application/json") -> None:
        # Will be implemented in Future PR
        pass

    def update_spatial_extent(self, item_bbox: List[float]) -> None:
        # Will be implemented in Future PR
        pass

    def update_temporal_extent(self, item_start_datetime: str, item_end_datetime: str) -> None:
        # Will be implemented in Future PR
        pass

    def update_extent(self, bbox: Optional[List[float]] = None, interval: Optional[List[str]] = None) -> None:
        # Will be implemented in Future PR
        pass
