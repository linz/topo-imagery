import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import shapely.geometry
import shapely.ops
import ulid

from scripts.files.files_helper import ContentType
from scripts.files.fs import write
from scripts.stac.imagery.capture_area import generate_capture_area, gsd_to_float
from scripts.stac.imagery.metadata_constants import (
    DATA_CATEGORIES,
    DEM,
    DSM,
    HUMAN_READABLE_REGIONS,
    RURAL_AERIAL_PHOTOS,
    SATELLITE_IMAGERY,
    SCANNED_AERIAL_PHOTOS,
    URBAN_AERIAL_PHOTOS,
    CollectionMetadata,
    MissingMetadataError,
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
        metadata: CollectionMetadata,
        collection_id: Optional[str] = None,
        providers: Optional[List[Provider]] = None,
    ) -> None:
        if not collection_id:
            collection_id = str(ulid.ULID())

        self.metadata = metadata

        self.stac = {
            "type": "Collection",
            "stac_version": STAC_VERSION,
            "id": collection_id,
            "title": self._title(),
            "description": self._description(),
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
            "providers": [],
            "linz:lifecycle": metadata["lifecycle"],
            "linz:geospatial_category": metadata["category"],
            "linz:region": metadata["region"],
            "linz:security_classification": "unclassified",
        }

        # Optional metadata
        if event_name := metadata.get("event_name"):
            self.stac["linz:event_name"] = event_name
        if geographic_description := metadata.get("geographic_description"):
            self.stac["linz:geographic_description"] = geographic_description

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

    def add_capture_area(self, polygons: List[shapely.geometry.shape], target: str, artifact_target: str = "/tmp") -> None:
        """Add the capture area of the Collection.
        The `href` or path of the capture-area.geojson is always set as the relative `./capture-area.geojson`

        Args:
            polygons: list of geometries
            target: location where the capture-area.geojson file will be saved
            artifact_target: location where the capture-area.geojson artifact file will be saved.
            This is useful for Argo Workflow in order to expose the file to the user for testing/validation purpose.
        """

        # The GSD is measured in meters (e.g., `0.3m`)
        capture_area_document = generate_capture_area(polygons, gsd_to_float(self.metadata["gsd"]))
        capture_area_content: bytes = json.dumps(capture_area_document).encode("utf-8")
        file_checksum = checksum.multihash_as_hex(capture_area_content)
        capture_area = {
            "href": f"./{CAPTURE_AREA_FILE_NAME}",
            "title": "Capture area",
            "type": ContentType.GEOJSON,
            "roles": ["metadata"],
            "file:checksum": file_checksum,
            "file:size": len(capture_area_content),
        }
        self.stac.setdefault("assets", {})["capture_area"] = capture_area

        # Save `capture-area.geojson` in target
        write(
            os.path.join(target, CAPTURE_AREA_FILE_NAME),
            capture_area_content,
            content_type=ContentType.GEOJSON.value,
        )

        # Save `capture-area.geojson` as artifact for Argo UI
        write(os.path.join(artifact_target, CAPTURE_AREA_FILE_NAME), capture_area_content)

        self.stac["stac_extensions"] = self.stac.get("stac_extensions", [])

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

        min_x = min(bbox[0], bbox[2], item_bbox[0], item_bbox[2])
        min_y = min(bbox[1], bbox[3], item_bbox[1], item_bbox[3])
        max_x = max(bbox[0], bbox[2], item_bbox[0], item_bbox[2])
        max_y = max(bbox[1], bbox[3], item_bbox[1], item_bbox[3])

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

        start_datetime = min(collection_datetimes[0], collection_datetimes[1], item_start)
        end_datetime = max(collection_datetimes[0], collection_datetimes[1], item_end)

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
        Satellite Imagery / Urban Aerial Photos / Rural Aerial Photos / Scanned Aerial Photos:
          https://github.com/linz/imagery/blob/master/docs/naming.md
        DEM / DSM:
          https://github.com/linz/elevation/blob/master/docs/naming.md
        Returns:
            Dataset Title
        """
        # format optional metadata
        geographic_description = self.metadata.get("geographic_description")
        historic_survey_number = self.metadata.get("historic_survey_number")

        # format date for metadata
        if (start_year := self.metadata["start_datetime"].year) == (end_year := self.metadata["end_datetime"].year):
            date = str(start_year)
        else:
            date = f"{start_year}-{end_year}"

        # determine dataset name
        region = HUMAN_READABLE_REGIONS[self.metadata["region"]]
        if geographic_description:
            imagery_name = geographic_description
            elevation_description = f"- {geographic_description}"
        else:
            imagery_name = region
            elevation_description = None

        # determine if dataset is preview
        if self.metadata.get("lifecycle") == "preview":
            preview = "- Preview"
        else:
            preview = None

        if self.metadata["category"] == SCANNED_AERIAL_PHOTOS:
            if not historic_survey_number:
                raise MissingMetadataError("historic_survey_number")
            return " ".join(
                value
                for value in [imagery_name, self.metadata["gsd"], historic_survey_number, f"({date})", preview or None]
                if value is not None
            )

        if self.metadata["category"] in [
            SATELLITE_IMAGERY,
            URBAN_AERIAL_PHOTOS,
            RURAL_AERIAL_PHOTOS,
        ]:
            return " ".join(
                value
                for value in [
                    imagery_name,
                    self.metadata["gsd"],
                    DATA_CATEGORIES[self.metadata["category"]],
                    f"({date})",
                    preview or None,
                ]
                if value is not None
            )
        if self.metadata["category"] in [DEM, DSM]:
            return " ".join(
                value
                for value in [
                    region,
                    elevation_description or None,
                    "LiDAR",
                    self.metadata["gsd"],
                    DATA_CATEGORIES[self.metadata["category"]],
                    f"({date})",
                    preview or None,
                ]
                if value is not None
            )
        raise SubtypeParameterError(self.metadata["category"])

    def _description(self) -> str:
        """Generates the descriptions for imagery and elevation datasets.
        Urban Aerial Photos / Rural Aerial Photos:
          Orthophotography within the [Region] region captured in the [year(s)] flying season.
        DEM / DSM:
          [Digital Surface Model / Digital Elevation Model] within the [Region] region captured in [year(s)].
        Satellite Imagery / Scanned Aerial Photos:
          [Satellite imagery | Scanned Aerial Photos] within the [Region] region captured in [year(s)].

        Returns:
            Dataset Description
        """
        # format date for metadata
        if (start_year := self.metadata["start_datetime"].year) == (end_year := self.metadata["end_datetime"].year):
            date = str(start_year)
        else:
            date = f"{start_year}-{end_year}"

        region = HUMAN_READABLE_REGIONS[self.metadata["region"]]

        if self.metadata["category"] == SCANNED_AERIAL_PHOTOS:
            desc = f"Scanned aerial imagery within the {region} region captured in {date}"
        elif self.metadata["category"] == SATELLITE_IMAGERY:
            desc = f"Satellite imagery within the {region} region captured in {date}"
        elif self.metadata["category"] in [URBAN_AERIAL_PHOTOS, RURAL_AERIAL_PHOTOS]:
            desc = f"Orthophotography within the {region} region captured in the {date} flying season"
        elif self.metadata["category"] == DEM:
            desc = f"Digital Elevation Model within the {region} region captured in {date}"
        elif self.metadata["category"] == DSM:
            desc = f"Digital Surface Model within the {region} region captured in {date}"
        else:
            raise SubtypeParameterError(self.metadata["category"])

        if event := self.metadata.get("event_name"):
            desc = desc + f", published as a record of the {event} event"

        return desc + "."
