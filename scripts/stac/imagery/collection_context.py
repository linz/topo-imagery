from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from scripts.stac.imagery.constants import (
    DATA_CATEGORIES,
    DEM,
    DEM_HILLSHADE,
    DEM_HILLSHADE_IGOR,
    DSM,
    DSM_HILLSHADE,
    DSM_HILLSHADE_IGOR,
    HUMAN_READABLE_REGIONS,
    LIFECYCLE_SUFFIXES,
    RURAL_AERIAL_PHOTOS,
    SATELLITE_IMAGERY,
    SCANNED_AERIAL_PHOTOS,
    URBAN_AERIAL_PHOTOS,
)
from scripts.stac.imagery.provider import Provider, ProviderRole, merge_provider_roles

GSD_UNIT = "m"


@dataclass
class CollectionContext:  # pylint:disable=too-many-instance-attributes
    """
    Holds contextual data and options used to create or update a STAC Collection.

    This class acts as a structured container for user-provided metadata when
    initializing an `ImageryCollection`. It does not represent a full STAC
    Collection but provides necessary information to generate one.
    It is used to generate titles and descriptions for datasets based on their metadata.
    It also provides a method to get the providers associated with the dataset.


    Attributes:
        category (str): The category of the dataset (e.g., "satellite-imagery").
        region (str): The region of the dataset (e.g., "auckland").
        gsd (Decimal): Ground Sample Distance in meters.
        start_datetime (datetime): Start date and time of the dataset.
        end_datetime (datetime): End date and time of the dataset.
        lifecycle (str): Lifecycle status of the dataset (e.g., "completed").
        linz_slug (str): LINZ slug for the dataset.
        producers (list[str]): List of producers for the dataset.
        licensors (list[str]): List of licensors for the dataset.
        collection_id (str | None): Collection ID, if applicable.
        geographic_description (str | None): Geographic description of the dataset.
        event_name (str | None): Event name, if applicable.
        historic_survey_number (str | None): Historic survey number, if applicable.
        add_title_suffix (bool): Whether to add a suffix based on lifecycle status.
        keep_title (bool): Whether to keep the original title.
        add_capture_dates (bool): Whether to link the capture dates file to the Collection.
        delete_existing_items (bool): Whether to delete existing items in the collection.
    """

    category: str
    region: str
    gsd: Decimal
    start_datetime: datetime
    end_datetime: datetime
    lifecycle: str
    linz_slug: str
    producers: list[str] = field(default_factory=list)
    licensors: list[str] = field(default_factory=list)
    collection_id: str | None = None
    geographic_description: str | None = None
    event_name: str | None = None
    historic_survey_number: str | None = None
    add_title_suffix: bool = True
    keep_title: bool = False
    add_capture_dates: bool = False
    delete_existing_items: bool = False

    @property
    def providers(self) -> list[Provider]:
        providers: list[Provider] = [
            {"name": "Toitū Te Whenua Land Information New Zealand", "roles": [ProviderRole.HOST, ProviderRole.PROCESSOR]}
        ]

        for producer_name in self.producers:
            providers.append({"name": producer_name, "roles": [ProviderRole.PRODUCER]})
        for licensor_name in self.licensors:
            providers.append({"name": licensor_name, "roles": [ProviderRole.LICENSOR]})
        return merge_provider_roles(providers)

    @property
    def title(self) -> str:
        """Generates the title for imagery and elevation datasets.
        Satellite Imagery / Urban Aerial Photos / Rural Aerial Photos / Scanned Aerial Photos:
          https://github.com/linz/imagery/blob/master/docs/naming.md
        DEM / DSM:
          https://github.com/linz/elevation/blob/master/docs/naming.md

        Raises:
            MissingMetadataError: if required metadata is missing
            SubtypeParameterError: if category is not recognised

        Returns:
            Dataset Title
        """
        # format optional metadata
        geographic_description = self.geographic_description
        historic_survey_number = self.historic_survey_number

        # format region
        region = HUMAN_READABLE_REGIONS[self.region]

        # format date
        start_year = self.start_datetime.year
        end_year = self.end_datetime.year
        date = f"({start_year})" if start_year == end_year else f"({start_year}-{end_year})"

        # format gsd
        gsd_str = f"{self.gsd}{GSD_UNIT}"

        # determine suffix based on its lifecycle
        lifecycle_suffix = LIFECYCLE_SUFFIXES.get(self.lifecycle, "") if self.add_title_suffix else None

        category = self.category

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

        elif category in {DEM_HILLSHADE, DEM_HILLSHADE_IGOR, DSM_HILLSHADE, DSM_HILLSHADE_IGOR}:
            components = [
                region,
                gsd_str,
                DATA_CATEGORIES[category],
            ]

        else:
            raise SubtypeParameterError(self.category)

        return " ".join(filter(None, components))

    @property
    def description(self) -> str:
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
        start_year = self.start_datetime.year
        end_year = self.end_datetime.year
        date = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"

        # format region
        region = HUMAN_READABLE_REGIONS[self.region]

        category = self.category
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
        elif category in {DEM_HILLSHADE, DEM_HILLSHADE_IGOR, DSM_HILLSHADE, DSM_HILLSHADE_IGOR}:
            desc = self._description_hillshade
        else:
            raise SubtypeParameterError(category)

        desc += f", published as a record of the {self.event_name} event." if self.event_name else "."

        return desc

    @property
    def _description_hillshade(self) -> str:
        """Generates the description for hillshade datasets."""

        region = HUMAN_READABLE_REGIONS[self.region]
        category = DATA_CATEGORIES[self.category]
        category_prefix = category[0:3]  # e.g. "dem" or "dsm"
        category_suffix = category[4:]  # e.g. "hillshade" or "hillshade-igor"
        gsd_str = f"{self.gsd}{GSD_UNIT}"

        if category_suffix == "Hillshade":
            shading_option = "GDAL’s default hillshading parameters of 315˚ azimuth and 45˚ elevation angle"
        else:
            shading_option = (
                "the -igor option in GDAL. "
                "This renders a softer hillshade that tries to minimize effects on other map features"
            )

        components = [
            "Hillshade generated from the",
            region,
            "LiDAR" if gsd_str != "8m" else "Contour-Derived",
            gsd_str,
            category_prefix,
            "using",
            shading_option,
        ]

        return " ".join(filter(None, components))


class SubtypeParameterError(Exception):
    def __init__(self, category: str) -> None:
        self.message = f"Unrecognised/Unimplemented Subtype Parameter: {category}"


class MissingMetadataError(Exception):
    def __init__(self, metadata: str) -> None:
        self.message = f"Missing metadata: {metadata}"
        self.message = f"Missing metadata: {metadata}"
