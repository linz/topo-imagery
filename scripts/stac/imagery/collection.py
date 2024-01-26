import json
import os
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

import shapely.geometry
import shapely.ops
import ulid

from scripts.files.files_helper import ContentType
from scripts.files.fs import read, write
from scripts.stac.imagery.capture_aera import generate_capture_area
from scripts.stac.imagery.metadata_constants import (
    HUMAN_READABLE_REGIONS,
    CollectionTitleMetadata,
    ElevationCategories,
    ImageryCategories,
    SubtypeParameterError,
)
from scripts.stac.imagery.provider import Provider, ProviderRole
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.stac_extensions import StacExtensions

CAPTURE_AREA_FILE_NAME = "capture-area.geojson"


class ImageryCollection:
    stac: Dict[str, Any]

    def __init__(
        self,
        title_metadata: CollectionTitleMetadata,
        collection_id: Optional[str] = None,
        providers: Optional[List[Provider]] = None,
    ) -> None:
        if not collection_id:
            collection_id = str(ulid.ULID())

        self.title_metadata = title_metadata

        self.stac = {
            "type": "Collection",
            "stac_version": STAC_VERSION,
            "id": collection_id,
            "title": self._title(),
            "description": self._description(),
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
            "providers": [],
        }

        # If the providers passed has already a LINZ provider: add its default roles to it
        has_linz = False
        if providers:
            linz = next((p for p in providers if p["name"] == "Toitū Te Whenua Land Information New Zealand"), None)
            if linz:
                linz["roles"].extend([ProviderRole.HOST, ProviderRole.PROCESSOR])
                has_linz = True
        else:
            providers = []

        if not has_linz:
            providers.append(
                {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.HOST, ProviderRole.PROCESSOR]}
            )

        self.add_providers(providers)

    def add_capture_area(self, polygons: List[shapely.geometry.shape], target: str) -> None:
        """Add the capture area of the Collection.
        The `href` or path of the capture-area.geojson is always set as the relative `./capture-area.geojson`

        Args:
            polygons: list of geometries
            target: path of the capture-area-geojson file
        """

        capture_area_content = generate_capture_area(polygons, float(self.title_metadata["gsd"].replace("m", "")))
        with TemporaryDirectory() as tmp_path:
            tmp_capture_area_path = os.path.join(tmp_path, CAPTURE_AREA_FILE_NAME)
            write(
                tmp_capture_area_path,
                json.dumps(capture_area_content).encode("utf-8"),
                content_type=ContentType.GEOJSON.value,
            )

            file_stats = os.stat(tmp_capture_area_path)
            file_checksum = checksum.multihash_as_hex(tmp_capture_area_path)
            capture_area = {
                "href": f"./{CAPTURE_AREA_FILE_NAME}",
                "title": "Capture area",
                "type": ContentType.GEOJSON,
                "roles": ["metadata"],
                "file:checksum": file_checksum,
                "file:size": file_stats.st_size,
            }
            self.stac.setdefault("assets", {})["capture_area"] = capture_area

            # Save `capture-area.geojson` in target
            write(
                os.path.join(target, CAPTURE_AREA_FILE_NAME),
                read(tmp_capture_area_path),
                content_type=ContentType.GEOJSON.value,
            )

        if not self.stac.get("stac_extensions"):
            self.stac["stac_extensions"] = []

        if StacExtensions.file.value not in self.stac["stac_extensions"]:
            self.stac["stac_extensions"].append(StacExtensions.file.value)

    def add_item(self, item: Dict[Any, Any]) -> None:
        """Add an `Item` to the `links` of the `Collection`.

        Args:
            item: STAC Item to add
        """
        item_self_link = next((feat for feat in item["links"] if feat["rel"] == "self"), None)
        if item_self_link:
            self.add_link(href=item_self_link["href"])
            self.update_temporal_extent(item["properties"]["start_datetime"], item["properties"]["end_datetime"])
            self.update_spatial_extent(item["bbox"])

    def add_link(self, href: str, rel: str = "item", file_type: str = "application/json") -> None:
        """Add a `link` to the existing `links` list of the Collection.

        Args:
            href: path
            rel: type of link. Defaults to "item".
            file_type: type of file pointed by the link. Defaults to "application/json".
        """
        self.stac["links"].append({"rel": rel, "href": href, "type": file_type})

    def add_providers(self, providers: List[Provider]) -> None:
        """Add a list of Providers to the existing list of `providers` of the Collection.

        Args:
            providers: a list of `Provider` objects
        """
        for p in providers:
            self.stac["providers"].append(p)

    def update_spatial_extent(self, item_bbox: List[float]) -> None:
        """Update (if needed) the Collection spatial extent from a bounding box.

        Args:
            item_bbox: bounding box of an item added to the Collection
        """
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
        """Update (if needed) the temporal extent of the collection.

        Args:
            item_start_datetime: start date of an item added to the Collection
            item_end_datetime: end date of an item added to the Collection
        """
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
        """Update an extent of the Collection whereas it's spatial or temporal.

        Args:
            bbox: bounding box. Defaults to None.
            interval: datetime interval. Defaults to None.
        """
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
        """Write the Collection in JSON format to the specified `destination`.

        Args:
            destination: path of the destination
        """
        write(destination, json.dumps(self.stac, ensure_ascii=False).encode("utf-8"), content_type=ContentType.JSON.value)

    def _title(self) -> str:
        """Generates the title for imagery and elevation datasets.
        Satellite Imagery / Urban Aerial Photos / Rural Aerial Photos:
          [Location / Region if no Location specified] [GSD] [?Event Name] [Data Sub-Type] ([Year(s)]) [?- Preview]
        DEM / DSM:
          [Location / Region if no Location specified] [?- Event Name] LiDAR [GSD] [Data Sub-Type] ([Year(s)]) [?- Preview]
        If Historic Survey Number:
          [Location / Region if no Location specified] [GSD] [Survey Number] ([Year(s)]) [?- Preview]

        Returns:
            Dataset Title
        """
        # format optional metadata
        location = self.title_metadata.get("location")
        historic_survey_number = self.title_metadata.get("historic_survey_number")
        event = self.title_metadata.get("event")

        # format date for metadata
        if self.title_metadata["start_datetime"].year == self.title_metadata["end_datetime"].year:
            date = str(self.title_metadata["start_datetime"].year)
        else:
            date = f"{self.title_metadata['start_datetime'].year}-{self.title_metadata['end_datetime'].year}"

        # determine dataset name
        if location:
            name = location
        else:
            name = HUMAN_READABLE_REGIONS[self.title_metadata["region"]]

        # determine if dataset is preview
        if self.title_metadata.get("lifecycle") == "preview":
            preview = "- Preview"
        else:
            preview = None

        if historic_survey_number:
            return " ".join(f"{name} {self.title_metadata['gsd']} {historic_survey_number} ({date}) {preview or ''}".split())

        if self.title_metadata["category"] in [ImageryCategories.SATELLITE, ImageryCategories.URBAN, ImageryCategories.RURAL]:
            return " ".join(
                f"{name} {self.title_metadata['gsd']} {event or ''} {self.title_metadata['category']} ({date}) {preview or ''}".split()  # pylint: disable=line-too-long
            )
        if self.title_metadata["category"] in [ElevationCategories.DEM, ElevationCategories.DSM]:
            return " ".join(
                f"{name} {self._elevation_title_event(event) or ''} LiDAR {self.title_metadata['gsd']} {self.title_metadata['category']} ({date}) {preview or ''}".split()  # pylint: disable=line-too-long
            )
        raise SubtypeParameterError(self.title_metadata["category"])

    def _elevation_title_event(self, event: Optional[str]) -> Optional[str]:
        if event:
            return f"- {event}"
        return None

    def _description(self) -> str:
        """Generates the descriptions for imagery and elevation datasets.
        Urban Aerial Photos / Rural Aerial Photos:
          Orthophotography within the [Region] region captured in the [Year(s)] flying season.
        DEM / DSM:
          [Digital Surface Model / Digital Elevation Model] within the [region] [?- location] region in [year(s)].
        Satellite Imagery:
          Satellite imagery within the [Region] region captured in [Year(s)].
        Historical Imagery:
          Scanned aerial imagery within the [Region] region captured in [Year(s)].

        Returns:
            Dataset Description
        """
        # format optional metadata
        location = self.title_metadata.get("location")
        historic_survey_number = self.title_metadata.get("historic_survey_number")
        event = self.title_metadata.get("event")

        # format date for metadata
        if self.title_metadata["start_datetime"].year == self.title_metadata["end_datetime"].year:
            date = str(self.title_metadata["start_datetime"].year)
        else:
            date = f"{self.title_metadata['start_datetime'].year}-{self.title_metadata['end_datetime'].year}"

        # format location for metadata description
        if location:
            location = f"- {location}"

        region = HUMAN_READABLE_REGIONS[self.title_metadata["region"]]

        if historic_survey_number:
            desc = f"Scanned aerial imagery within the {region} region captured in {date}"
        elif self.title_metadata["category"] == ImageryCategories.SATELLITE:
            desc = f"Satellite imagery within the {region} region captured in {date}"
        elif self.title_metadata["category"] in [ImageryCategories.URBAN, ImageryCategories.RURAL]:
            desc = f"Orthophotography within the {region} region captured in the {date} flying season"
        elif self.title_metadata["category"] == ElevationCategories.DEM:
            desc = " ".join(f"Digital Elevation Model within the {region} {location or ''} region in {date}".split())
        elif self.title_metadata["category"] == ElevationCategories.DSM:
            desc = " ".join(f"Digital Surface Model within the {region} {location or ''} region in {date}".split())
        else:
            raise SubtypeParameterError(self.title_metadata["category"])

        if event:
            desc = desc + f", published as a record of the {event} event"

        return desc + "."
