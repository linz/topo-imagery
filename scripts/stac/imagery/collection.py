import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import ulid

from scripts.files.fs import write
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.util.STAC_VERSION import STAC_VERSION


class ImageryCollection:
    stac: Dict[str, Any]

    def __init__(
        self, title: str, description: str, collection_id: Optional[str] = None, providers: Optional[List[Provider]] = None
    ) -> None:
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
            "providers": [],
        }

        # If the providers passed has already a LINZ provider: add its default roles to it
        has_linz = False
        if providers:
            linz = next((p for p in providers if p["name"] == "Toitū Te Whenua Land Information New Zealand"), None)
            if linz:
                print("FOUND IT")
                linz["roles"].extend([ProviderRole.HOST, ProviderRole.PROCESSOR])
                has_linz = True
            print("NOT FOUND")
        else:
            providers = []

        if not has_linz:
            providers.append(
                {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.HOST, ProviderRole.PROCESSOR]}
            )

        self.add_providers(providers)

    def add_item(self, item: Dict[Any, Any]) -> None:
        item_self_link = next((feat for feat in item["links"] if feat["rel"] == "self"), None)
        if item_self_link:
            self.add_link(href=item_self_link["href"])
            self.update_temporal_extent(item["properties"]["start_datetime"], item["properties"]["end_datetime"])
            self.update_spatial_extent(item["bbox"])

    def add_link(self, href: str, rel: str = "item", file_type: str = "application/json") -> None:
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})

    def add_providers(self, providers: List[Provider]) -> None:
        for p in providers:
            self.stac["providers"].append(p)

    def update_spatial_extent(self, item_bbox: List[float]) -> None:
        if "extent" not in self.stac:
            self.update_extent(bbox=item_bbox)
            return
        if self.stac["extent"]["spatial"]["bbox"] == [None]:
            self.update_extent(bbox=item_bbox)
            return

        bbox = self.stac["extent"]["spatial"]["bbox"][0]

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
        if self.stac["extent"]["temporal"]["interval"] == [None]:
            self.update_extent(interval=[item_start_datetime, item_end_datetime])
            return

        interval = self.stac["extent"]["temporal"]["interval"][0]

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
                    "bbox": [bbox],
                },
                "temporal": {"interval": [interval]},
            }
            return
        if bbox:
            self.stac["extent"]["spatial"]["bbox"] = [bbox]
        if interval:
            self.stac["extent"]["temporal"]["interval"] = [interval]

    def write_to(self, destination: str) -> None:
        write(destination, json.dumps(self.stac, ensure_ascii=False).encode("utf-8"))
