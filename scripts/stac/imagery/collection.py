import json
import os
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
from scripts.stac.imagery.metadata_constants import (
    DATA_CATEGORIES,
    DEM,
    DEM_HILLSHADE,
    DEM_HILLSHADE_IGOR,
    DSM,
    HUMAN_READABLE_REGIONS,
    LIFECYCLE_SUFFIXES,
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
from scripts.stac.util.media_type import StacMediaType
from scripts.stac.util.stac_extensions import StacExtensions

CAPTURE_AREA_FILE_NAME = "capture-area.geojson"
CAPTURE_DATES_FILE_NAME = "capture-dates.geojson"
GSD_UNIT = "m"


class ImageryCollection:
    stac: dict[str, Any]
    capture_area: dict[str, Any] | None = None
    published_location: str | None = None

    def __init__(
        self,
        metadata: CollectionMetadata,
        created_datetime: str,
        updated_datetime: str,
        linz_slug: str,
        collection_id: str | None = None,
        providers: list[Provider] | None = None,
        add_title_suffix: bool = True,
    ) -> None:
        if not collection_id:
            collection_id = str(ulid.ULID())

        self.metadata = metadata

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
            "created": created_datetime,
            "updated": updated_datetime,
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

    @classmethod
    def from_file(cls, file_name: str, metadata: CollectionMetadata, updated_datetime: str) -> "ImageryCollection":
        """Load an ImageryCollection from a Collection file.

        Args:
            file_name: The s3 URL or local path of the Collection file to load.

        Returns:
            The loaded ImageryCollection.
        """
        file_content = read(file_name)
        stac_from_file = json.loads(file_content.decode("UTF-8"))
        stac_from_file["updated"] = updated_datetime
        collection = cls(
            metadata=metadata,
            created_datetime=stac_from_file["created"],
            updated_datetime=stac_from_file["updated"],
            linz_slug=stac_from_file["linz:slug"],
        )
        # Override STAC from the original collection
        collection.stac = stac_from_file

        collection.published_location = os.path.dirname(file_name)
        capture_area_path = os.path.join(collection.published_location, CAPTURE_AREA_FILE_NAME)
        # Some published datasets may not have a capture-area.geojson file (TDE-988)
        if exists(capture_area_path):
            collection.capture_area = json.loads(read(capture_area_path))

        return collection

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
        # If published dataset update, merge the existing capture area with the new one
        if self.capture_area:
            polygons.append(shape(self.capture_area["geometry"]))
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
        """Get the STAC Items from the Collection.

        Returns:
            a list of STAC Items
        """
        if not self.published_location:
            get_log().info("Collection is not published.")
            return []
        items_stac = []
        for link in self.stac.get("links", []):
            if link["rel"] != Relation.ITEM:
                continue
            item_path = os.path.join(self.published_location, os.path.basename(link["href"]))
            if not exists(item_path):
                # TODO: should we raise an error here?
                get_log().warn(f"Item not found: {item_path}")
                continue
            existing_item_stac = json.loads(read(item_path))
            items_stac.append(existing_item_stac)
        return items_stac

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
            add_suffix: Whether to add a suffix based on the lifecycle. For example, " - Preview". Defaults to True.

        Raises:
            MissingMetadataError: if required metadata is missing
            SubtypeParameterError: if category is not recognised

        Returns:
            Dataset Title
        """
        # format optional metadata
        geographic_description = self.metadata.get("geographic_description")
        historic_survey_number = self.metadata.get("historic_survey_number")

        # format region
        region = HUMAN_READABLE_REGIONS[self.metadata["region"]]

        # format date
        start_year = self.metadata["start_datetime"].year
        end_year = self.metadata["end_datetime"].year
        date = f"({start_year})" if start_year == end_year else f"({start_year}-{end_year})"

        # format gsd
        gsd_str = f"{self.metadata['gsd']}{GSD_UNIT}"

        # determine suffix based on its lifecycle
        lifecycle_suffix = LIFECYCLE_SUFFIXES.get(self.metadata.get("lifecycle", "")) if add_suffix else None

        category = self.metadata["category"]

        if category == SCANNED_AERIAL_PHOTOS:
            if not historic_survey_number:
                raise MissingMetadataError("historic_survey_number")
            components = [
                geographic_description or region,
                gsd_str,
                historic_survey_number,
                date,
                lifecycle_suffix,
            ]

        elif category in {SATELLITE_IMAGERY, URBAN_AERIAL_PHOTOS, RURAL_AERIAL_PHOTOS}:
            components = [
                geographic_description or region,
                gsd_str,
                DATA_CATEGORIES[category],
                date,
                lifecycle_suffix,
            ]

        elif category in {DEM, DSM}:
            components = [
                region,
                "-" if geographic_description else None,
                geographic_description,
                "LiDAR",
                gsd_str,
                DATA_CATEGORIES[category],
                date,
                lifecycle_suffix,
            ]

        elif category in {DEM_HILLSHADE, DEM_HILLSHADE_IGOR}:
            components = [
                region,
                gsd_str if self.metadata["gsd"] == 8 else None,
                "DEM Hillshade",
                "- Igor" if category == DEM_HILLSHADE_IGOR else None,
            ]

        else:
            raise SubtypeParameterError(self.metadata["category"])

        return " ".join(filter(None, components))

    def _description(self) -> str:
        """Generates the descriptions for imagery and elevation datasets.
        Urban Aerial Photos / Rural Aerial Photos:
          Orthophotography within the [Region] region captured in the [year(s)] flying season.
        DEM / DSM:
          [Digital Surface Model / Digital Elevation Model] within the [Region] region captured in [year(s)].
        DEM_HILLSHADE / DEM_HILLSHADE_IGOR:
          [Digital Elevation Model] [mono-directional / whiter multi-directional] hillshade derived from 1m LiDAR.
          Gaps filled with lower resolution elevation data (8m contour) as needed.
        Satellite Imagery / Scanned Aerial Photos:
          [Satellite imagery | Scanned Aerial Photos] within the [Region] region captured in [year(s)].

        Returns:
            Dataset Description
        """
        # format date
        start_year = self.metadata["start_datetime"].year
        end_year = self.metadata["end_datetime"].year
        date = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"

        # format region
        region = HUMAN_READABLE_REGIONS[self.metadata["region"]]

        category = self.metadata["category"]
        if category in {URBAN_AERIAL_PHOTOS, RURAL_AERIAL_PHOTOS}:
            date = f"the {date} flying season"

        base_descriptions = {
            SCANNED_AERIAL_PHOTOS: "Scanned aerial imagery",
            SATELLITE_IMAGERY: "Satellite imagery",
            URBAN_AERIAL_PHOTOS: "Orthophotography",
            RURAL_AERIAL_PHOTOS: "Orthophotography",
            DEM: "Digital Elevation Model",
            DSM: "Digital Surface Model",
        }

        if category in base_descriptions:
            desc = f"{base_descriptions[category]} within the {region} region captured in {date}"
        elif category.startswith(DEM_HILLSHADE):
            desc = self._hillshade_description()
        else:
            raise SubtypeParameterError(category)

        if event := self.metadata.get("event_name"):
            desc = f"{desc}, published as a record of the {event} event."
        else:
            desc = f"{desc}."

        return desc

    def _hillshade_description(self) -> str:
        """Generates the description for hillshade datasets."""

        region = HUMAN_READABLE_REGIONS[self.metadata["region"]]
        category = self.metadata["category"]
        gsd_str = f"{self.metadata["gsd"]}{GSD_UNIT}"

        if category == DEM_HILLSHADE_IGOR:
            shading_option = (
                "the -igor option in GDAL. "
                "This renders a softer hillshade that tries to minimize effects on other map features"
            )
        else:
            shading_option = "GDAL’s default hillshading parameters of 315˚ azimuth and 45˚ elevation angle"

        compontents = [
            "Hillshade generated from the",
            f"{region} LiDAR {gsd_str} DEM and" if gsd_str != "8m" else None,
            f"{region} Contour-Derived 8m DEM",
            f"(where no {self.metadata["gsd"]}m DEM data exists)" if gsd_str != "8m" else None,
            "using",
            shading_option,
        ]

        return " ".join(filter(None, compontents))

    def remove_item_geometry_from_capture_area(self, item: dict[str, Any]) -> None:
        """Remove the geometry of an Item from the capture area of the Collection.

        Args:
            item: an Item to remove from the capture area
        """
        if not self.capture_area:
            get_log().warn(
                "No capture area found",
                action="remove_item_geometry_from_capture_area",
                reason="skip",
            )
            return
        item_geometry = shape(item["geometry"])
        capture_area_geometry = shape(self.capture_area["geometry"])
        updated_capture_area_geometry = capture_area_geometry.difference(item_geometry)
        self.capture_area["geometry"] = json.loads(to_geojson(updated_capture_area_geometry))
