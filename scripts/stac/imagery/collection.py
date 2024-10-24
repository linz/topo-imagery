import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

import ulid
from shapely.geometry.base import BaseGeometry

from scripts.datetimes import format_rfc_3339_datetime_string, parse_rfc_3339_datetime
from scripts.files.files_helper import ContentType
from scripts.files.fs import read, write
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.capture_area import generate_capture_area
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
from scripts.stac.imagery.provider import Provider, ProviderRole, merge_provider_roles
from scripts.stac.link import Link, Relation
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.linz_slug import create_linz_slug
from scripts.stac.util.media_type import StacMediaType
from scripts.stac.util.stac_extensions import StacExtensions

CAPTURE_AREA_FILE_NAME = "capture-area.geojson"
CAPTURE_DATES_FILE_NAME = "capture-dates.geojson"


class ImageryCollection:
    stac: dict[str, Any]

    def __init__(
        self,
        metadata: CollectionMetadata,
        now: Callable[[], datetime],
        collection_id: str | None = None,
        providers: list[Provider] | None = None,
        add_title_suffix: bool = True,
        linz_slug: str | None = None,
    ) -> None:
        if not linz_slug:
            linz_slug = create_linz_slug(metadata)
        if not collection_id:
            collection_id = str(ulid.ULID())

        self.metadata = metadata

        now_string = format_rfc_3339_datetime_string(now())
        self.stac = {
            "type": "Collection",
            "stac_version": STAC_VERSION,
            "id": collection_id,
            "title": self._title(add_title_suffix),
            "description": self._description(),
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
            "providers": [],
            "linz:lifecycle": metadata["lifecycle"],
            "linz:geospatial_category": metadata["category"],
            "linz:region": metadata["region"],
            "linz:security_classification": "unclassified",
            "linz:slug": linz_slug,
            "created": now_string,
            "updated": now_string,
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

        self.add_providers(merge_provider_roles(providers))

    def add_capture_area(self, polygons: list[BaseGeometry], target: str, artifact_target: str = "/tmp") -> None:
        """Add the capture area of the Collection.
        The `href` or path of the capture-area.geojson is always set as the relative `./capture-area.geojson`

        Args:
            polygons: list of BaseGeometries
            target: location where the capture-area.geojson file will be saved
            artifact_target: location where the capture-area.geojson artifact file will be saved.
            This is useful for Argo Workflow in order to expose the file to the user for testing/validation purpose.
        """

        # The GSD is measured in meters (e.g., `0.3m`)
        capture_area_document = generate_capture_area(polygons, self.metadata["gsd"])
        capture_area_content: bytes = dict_to_json_bytes(capture_area_document)
        file_checksum = checksum.multihash_as_hex(capture_area_content)
        capture_area = {
            "href": f"./{CAPTURE_AREA_FILE_NAME}",
            "title": "Capture area",
            "description": "Boundary of the total capture area for this collection. Excludes nodata areas in the source "
            "data. Geometries are simplified.",
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

    def add_capture_dates(self, source_directory: str) -> None:
        """Add the capture dates metadata file for the National 1m DEM dataset.
        The `href` or path of capture-dates.geojson is always set as the relative `./capture-dates.geojson`

        Args:
            source_directory: the location of the capture-dates.geojson file to be linked
        """

        capture_dates_content = read(os.path.join(source_directory, CAPTURE_DATES_FILE_NAME))
        file_checksum = checksum.multihash_as_hex(capture_dates_content)
        capture_dates = {
            "href": f"./{CAPTURE_DATES_FILE_NAME}",
            "title": "Capture dates",
            "description": "Boundaries of individual surveys or flight runs that make up the overall collection with "
            "the data collection dates, data source links and other associated metadata, such as producers and licensors, "
            "where available. Excludes nodata areas in the source data. Geometries are simplified.",
            "type": ContentType.GEOJSON,
            "roles": ["metadata"],
            "file:checksum": file_checksum,
            "file:size": len(capture_dates_content),
        }
        self.stac.setdefault("assets", {})["capture_dates"] = capture_dates

    def add_item(self, item: dict[Any, Any]) -> None:
        """Add an `Item` to the `links` of the `Collection`.

        Args:
            item: STAC Item to add
        """
        item_self_link = next((feat for feat in item["links"] if feat["rel"] == "self"), None)
        if item_self_link:
            self.stac["links"].append(
                Link(
                    path=item_self_link["href"],
                    rel=Relation.ITEM,
                    media_type=StacMediaType.GEOJSON,
                    file_content=dict_to_json_bytes(item),
                ).stac
            )
            self.update_temporal_extent(item["properties"]["start_datetime"], item["properties"]["end_datetime"])
            self.update_spatial_extent(item["bbox"])

    def add_providers(self, providers: list[Provider]) -> None:
        """Add a list of Providers to the existing list of `providers` of the Collection.
        The provider roles are sorted alphabetically.

        Args:
            providers: a list of `Provider` objects
        """
        for p in providers:
            p["roles"] = sorted(p["roles"])
            self.stac["providers"].append(p)

    def update_spatial_extent(self, item_bbox: list[float]) -> None:
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

        item_start = parse_rfc_3339_datetime(item_start_datetime)
        item_end = parse_rfc_3339_datetime(item_end_datetime)

        collection_datetimes = []
        for date in interval:
            collection_datetimes.append(parse_rfc_3339_datetime(date))

        start_datetime = min(collection_datetimes[0], collection_datetimes[1], item_start)
        end_datetime = max(collection_datetimes[0], collection_datetimes[1], item_end)

        self.update_extent(
            interval=[
                format_rfc_3339_datetime_string(start_datetime),
                format_rfc_3339_datetime_string(end_datetime),
            ]
        )

    def update_extent(self, bbox: list[float] | None = None, interval: list[str] | None = None) -> None:
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
        write(destination, dict_to_json_bytes(self.stac), content_type=ContentType.JSON.value)

    def _title(self, add_suffix: bool = True) -> str:
        """Generates the title for imagery and elevation datasets.
        Satellite Imagery / Urban Aerial Photos / Rural Aerial Photos / Scanned Aerial Photos:
          https://github.com/linz/imagery/blob/master/docs/naming.md
        DEM / DSM:
          https://github.com/linz/elevation/blob/master/docs/naming.md

        Args:
            add_suffix: Weither to add a suffix based on the lifecycle. For example, " - Preview". Defaults to True.

        Raises:
            MissingMetadataError: if required metadata is missing
            SubtypeParameterError: if category is not recognised

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

        # determine if the dataset title requires a suffix based on its lifecycle
        lifecycle_suffix = None
        if add_suffix:
            if self.metadata.get("lifecycle") == "preview":
                lifecycle_suffix = "- Preview"
            elif self.metadata.get("lifecycle") == "ongoing":
                lifecycle_suffix = "- Draft"

        if self.metadata["category"] == SCANNED_AERIAL_PHOTOS:
            if not historic_survey_number:
                raise MissingMetadataError("historic_survey_number")
            return " ".join(
                value
                for value in [
                    imagery_name,
                    f"{self.metadata['gsd']}{GSD_UNIT}",
                    historic_survey_number,
                    f"({date})",
                    lifecycle_suffix,
                ]
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
                    f"{self.metadata['gsd']}{GSD_UNIT}",
                    DATA_CATEGORIES[self.metadata["category"]],
                    f"({date})",
                    lifecycle_suffix,
                ]
                if value is not None
            )
        if self.metadata["category"] in [DEM, DSM]:
            return " ".join(
                value
                for value in [
                    region,
                    elevation_description,
                    "LiDAR",
                    f"{self.metadata['gsd']}{GSD_UNIT}",
                    DATA_CATEGORIES[self.metadata["category"]],
                    f"({date})",
                    lifecycle_suffix,
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


GSD_UNIT = "m"
