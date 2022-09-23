from typing import Any, Dict, List, Optional

import ulid

from scripts.stac.util.STAC_VERSION import STAC_VERSION


class ImageryCollection:
    stac: Dict[str, Any]

    def __init__(
        self, title: Optional[str] = None, description: Optional[str] = None, stac: Optional[Dict[str, Any]] = None
    ) -> None:
        if stac:
            self.stac = stac
        elif title and description:
            self.stac = {
                "type": "Collection",
                "stac_version": STAC_VERSION,
                "id": str(ulid.ULID()),
                "title": title,
                "description": description,
                "license": "CC-BY-4.0",
                "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
            }
        else:
            raise Exception("incorrect initialising parameters must have 'stac' or 'title and description'")

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
