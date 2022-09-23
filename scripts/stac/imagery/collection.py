from datetime import datetime
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
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})

    def update_spatial_extent(self, item_bbox: List[float]) -> None:
        if "extent" not in self.stac:
            self.update_extent(bbox=item_bbox)
            return
        if not self.stac["extent"]["spatial"]["bbox"]:
            self.update_extent(bbox=item_bbox)
            return

        bbox = self.stac["extent"]["spatial"]["bbox"]
        min_x = min(bbox[0], bbox[2])
        max_x = max(bbox[0], bbox[2])
        min_y = min(bbox[1], bbox[3])
        max_y = max(bbox[1], bbox[3])

        item_min_x = min(item_bbox[0], item_bbox[2])
        item_max_x = max(item_bbox[0], item_bbox[2])
        item_min_y = min(item_bbox[1], item_bbox[3])
        item_max_y = max(item_bbox[1], item_bbox[3])

        if item_min_x < min_x:
            min_x = item_min_x
        if item_min_y < min_y:
            min_y = item_min_y
        if item_max_x > max_x:
            max_x = item_max_x
        if item_max_y > max_y:
            max_y = item_max_y

        self.update_extent(bbox=[min_x, min_y, max_x, max_y])

    def update_temporal_extent(self, item_start_datetime: str, item_end_datetime: str) -> None:
        if "extent" not in self.stac:
            self.update_extent(interval=[item_start_datetime, item_end_datetime])
            return
        if not self.stac["extent"]["temporal"]["interval"]:
            self.update_extent(interval=[item_start_datetime, item_end_datetime])
            return

        interval = self.stac["extent"]["temporal"]["interval"]

        item_start = datetime.strptime(item_start_datetime, "%Y-%m-%dT%H:%M:%SZ")
        item_end = datetime.strptime(item_end_datetime, "%Y-%m-%dT%H:%M:%SZ")

        collection_datetimes = []
        for date in interval:
            collection_datetimes.append(datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))

        start_datetime = min(collection_datetimes[0], collection_datetimes[1])
        end_datetime = max(collection_datetimes[0], collection_datetimes[1])

        if item_start < start_datetime:
            start_datetime = item_start
        if item_end > end_datetime:
            end_datetime = item_end

        self.update_extent(
            interval=[
                start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ]
        )

    def update_extent(self, bbox: Optional[List[float]] = None, interval: Optional[List[str]] = None) -> None:
        if "extent" not in self.stac:
            self.stac["extent"] = {
                "spatial": {
                    "bbox": bbox,
                },
                "temporal": {"interval": interval},
            }
            return
        if bbox:
            self.stac["extent"]["spatial"]["bbox"] = bbox
        if interval:
            self.stac["extent"]["temporal"]["interval"] = interval