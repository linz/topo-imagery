import json
import os
from decimal import Decimal
from typing import Any

import ulid
from linz_logger import get_log
from shapely import to_geojson
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from scripts.datetimes import format_rfc_3339_datetime_string, parse_rfc_3339_datetime
from scripts.files.files_helper import ContentType
from scripts.files.fs import exists, read, write
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.capture_area import generate_capture_area
from scripts.stac.imagery.collection_context import CollectionContext
from scripts.stac.imagery.provider import Provider
from scripts.stac.link import Link, Relation
from scripts.stac.util import checksum
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.media_type import StacMediaType
from scripts.stac.util.stac_extensions import StacExtensions

COLLECTION_FILE_NAME = "collection.json"
CAPTURE_AREA_FILE_NAME = "capture-area.geojson"
CAPTURE_DATES_FILE_NAME = "capture-dates.geojson"
WARN_NO_PUBLISHED_CAPTURE_AREA = "no_published_capture_area"


class ImageryCollection:
    stac: dict[str, Any]
    gsd: Decimal
    capture_area: dict[str, Any] | None = None
    published_location: str | None = None

    def __init__(
        self,
        context: CollectionContext,
        created_datetime: str,
        updated_datetime: str,
    ) -> None:
        if not context.collection_id:
            context.collection_id = str(ulid.ULID())

        self.gsd = context.gsd

        self.stac = {
            "type": "Collection",
            "stac_version": STAC_VERSION,
            "id": context.collection_id,
            "title": context.get_title(),
            "description": context.get_description(),
            "license": "CC-BY-4.0",
            "links": [{"rel": "self", "href": "./collection.json", "type": "application/json"}],
            "providers": [],
            "linz:lifecycle": context.lifecycle,
            "linz:geospatial_category": context.category,
            "linz:region": context.region,
            "linz:security_classification": "unclassified",
            "linz:slug": context.linz_slug,
            "created": created_datetime,
            "updated": updated_datetime,
        }

        # Optional metadata - if not provided, the field will not be added to the Collection
        if event_name := context.event_name:
            self.stac["linz:event_name"] = event_name
        if geographic_description := context.geographic_description:
            self.stac["linz:geographic_description"] = geographic_description

        self.add_providers(context.get_providers())

    @classmethod
    def from_file(cls, path: str) -> "ImageryCollection":
        """Load an ImageryCollection object from a STAC Collection file.

        Args:
            path: The path to the STAC Collection file to load.
            metadata: The metadata of the Collection.

        Returns:
            The ImageryCollection loaded from the file.
        """
        file_content = read(path)
        stac_from_file = json.loads(file_content.decode("UTF-8"))
        collection = cls.__new__(cls)
        collection.stac = stac_from_file
        collection.published_location = os.path.dirname(path)
        capture_area_path = os.path.join(collection.published_location, CAPTURE_AREA_FILE_NAME)
        # Some published datasets may not have a capture-area.geojson file (TDE-988)
        if exists(capture_area_path):
            collection.capture_area = json.loads(read(capture_area_path))
        return collection

    def update(self, context: CollectionContext, updated_datetime: str, keep_title_description: bool = False) -> None:
        """Update the Collection with new metadata.

        Args:
            context: The context containing the updated metadata.
            updated_datetime: The updated datetime of the Collection.
            keep_title_desc: Whether to keep the original title and description.
        """
        if context.lifecycle:
            self.stac["linz:lifecycle"] = context.lifecycle
        if context.category:
            self.stac["linz:geospatial_category"] = context.category
        if context.region:
            self.stac["linz:region"] = context.region
        if context.geographic_description:
            self.stac["linz:geographic_description"] = context.geographic_description
        if context.event_name:
            self.stac["linz:event_name"] = context.event_name
        if context.historic_survey_number:
            self.stac["linz:historic_survey_number"] = context.historic_survey_number
        if context.producers or context.licensors:
            self.stac["providers"] = []
            self.add_providers(context.get_providers())
        if not keep_title_description:
            self.stac["title"] = context.get_title()
            self.stac["description"] = context.get_description()

        self.stac["updated"] = updated_datetime
        self.gsd = context.gsd

    def add_capture_area(self, polygons: list[BaseGeometry], target: str, artifact_target: str = "/tmp") -> None:
        """Add the capture area of the Collection.
        If the Collection is an update of a published dataset, the existing capture area will be merged with the new one.
        The `href` or path of the capture-area.geojson is always set as the relative `./capture-area.geojson`

        Args:
            polygons: list of BaseGeometries
            target: location where the capture-area.geojson file will be saved
            artifact_target: location where the capture-area.geojson artifact file will be saved.
            This is useful for Argo Workflow in order to expose the file to the user for testing/validation purpose.
        """
        # If published dataset does not have a capture-area,
        # system should skip its creation as it may miss existing Item footprints
        if self.published_location and not self.capture_area:
            get_log().warn(
                f"{WARN_NO_PUBLISHED_CAPTURE_AREA}: a new capture-area can't be generated.",
            )
            return
        # If published dataset update, merge the existing capture area with the new one
        if self.capture_area:
            polygons.append(shape(self.capture_area["geometry"]))
        # The GSD is measured in meters (e.g., `0.3m`)
        capture_area_document = generate_capture_area(polygons, self.gsd)
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
        Update the spatial and temporal extent of the `Collection` based on the `Item` bounding box and datetime.

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
        if not self.stac.get("extent", {}).get("spatial", {}).get("bbox"):
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
        if not self.stac.get("extent", {}).get("temporal", {}).get("interval"):
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
            self.reset_extent()
        if bbox:
            self.stac["extent"]["spatial"]["bbox"] = [bbox]
        if interval:
            self.stac["extent"]["temporal"]["interval"] = [interval]

    def reset_extent(self) -> None:
        """Reset the spatial and temporal extents of the Collection."""
        self.stac.setdefault("extent", {}).setdefault("spatial", {})["bbox"] = None
        self.stac.setdefault("extent", {}).setdefault("temporal", {})["interval"] = None

    def get_items_stac(self) -> list[dict[str, Any]]:
        """Get the STAC Items content from the Collection links.

        Returns:
            a list of STAC Item contents
        """
        if not self.published_location:
            get_log().info("Collection is not published: no STAC Item to load.")
            return []
        items_stac = []
        for link in self.stac.get("links", []):
            if link["rel"] != Relation.ITEM:
                continue
            item_path = os.path.join(self.published_location, os.path.basename(link["href"]))
            if not exists(item_path):
                get_log().error(f"STAC Item not found: {item_path}")
                raise FileNotFoundError(item_path)
            existing_item_stac = json.loads(read(item_path))
            items_stac.append(existing_item_stac)
        return items_stac

    def write_to(self, destination: str) -> None:
        """Write the Collection in JSON format to the specified `destination`.

        Args:
            destination: path of the destination
        """
        write(destination, dict_to_json_bytes(self.stac), content_type=ContentType.JSON.value)

    def remove_item_geometry_from_capture_area(self, item: dict[str, Any]) -> None:
        """Remove the geometry of an Item from the capture area of the Collection.
        The Item's geometry, usually tile shape (covering total or more of the footprint),
        is removed from the capture area in case of the resupplied Item footprint is not covering the former Item's footprint.

        Args:
            item: an Item to remove from the capture area
        """
        if not self.capture_area:
            get_log().warn(
                WARN_NO_PUBLISHED_CAPTURE_AREA,
            )
            return
        item_geometry = shape(item["geometry"])
        capture_area_geometry = shape(self.capture_area["geometry"])
        updated_capture_area_geometry = capture_area_geometry.difference(item_geometry)
        self.capture_area["geometry"] = json.loads(to_geojson(updated_capture_area_geometry))
