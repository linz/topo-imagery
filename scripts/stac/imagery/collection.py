from datetime import datetime
from typing import Any, Dict, List, Optional

import ulid

from scripts.stac.util.STAC_VERSION import STAC_VERSION


class ImageryCollection:
    stac: Dict[str, Any]

    def __init__(self, title: str, description: str, collection_id: Optional[str] = None) -> None:
        if not collection_id:
            collection_id = str(ulid.ULID())

        self.stac = {
            "type": "Collection",
            "stac_version": STAC_VERSION,
            "id": collection_id,
            "title": title,
            "description": description,
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
        }

    def add_item(self, item: Dict[Any, Any]) -> None:

        item_self_link = next((feat for feat in item["links"] if feat["rel"] == "self"), None)
        if item_self_link:
            self.add_link(href=item_self_link["href"])
            self.update_temporal_extent(item["properties"]["start_datetime"], item["properties"]["end_datetime"])
            self.update_spatial_extent(item["bbox"])

    def add_link(self, href: str, rel: str = "item", file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})

    def update_spatial_extent(self, input_bbox: List[float]) -> None:
        if "extent" not in self.stac:
            self.update_extent(bbox=input_bbox)
            return
        if self.stac["extent"]["spatial"]["bbox"] == [None]:
            self.update_extent(bbox=input_bbox)
            return

        bbox = self.stac["extent"]["spatial"]["bbox"][0]

        min_x = min(bbox[0], bbox[2])
        max_x = max(bbox[0], bbox[2])
        min_y = min(bbox[1], bbox[3])
        max_y = max(bbox[1], bbox[3])

        input_min_x = min(input_bbox[0], input_bbox[2])
        input_max_x = max(input_bbox[0], input_bbox[2])
        input_min_y = min(input_bbox[1], input_bbox[3])
        input_max_y = max(input_bbox[1], input_bbox[3])

        if input_min_x < min_x:
            min_x = input_min_x
        if input_min_y < min_y:
            min_y = input_min_y
        if input_max_x > max_x:
            max_x = input_max_x
        if input_max_y > max_y:
            max_y = input_max_y

        self.update_extent(bbox=[min_x, min_y, max_x, max_y])

    def update_temporal_extent(self, input_start_datetime: str, input_end_datetime: str) -> None:
        if "extent" not in self.stac:
            self.update_extent(interval=[input_start_datetime, input_end_datetime])
            return
        if self.stac["extent"]["temporal"]["interval"] == [None]:
            self.update_extent(interval=[input_start_datetime, input_end_datetime])
            return

        input_start = datetime.strptime(input_start_datetime, "%Y-%m-%dT%H:%M:%SZ")
        input_end = datetime.strptime(input_end_datetime, "%Y-%m-%dT%H:%M:%SZ")

        collection_datetimes = []
        interval = self.stac["extent"]["temporal"]["interval"][0]
        for date in interval:
            collection_datetimes.append(datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))

        start_datetime = min(collection_datetimes[0], collection_datetimes[1])
        end_datetime = max(collection_datetimes[0], collection_datetimes[1])

        if input_start < start_datetime:
            start_datetime = input_start
        if input_end > end_datetime:
            end_datetime = input_end

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
                    "bbox": [bbox],
                },
                "temporal": {"interval": [interval]},
            }
            return
        if bbox:
            self.stac["extent"]["spatial"]["bbox"] = [bbox]
        if interval:
            self.stac["extent"]["temporal"]["interval"] = [interval]
