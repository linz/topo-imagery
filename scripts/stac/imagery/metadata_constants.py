from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class CollectionMetadata:  # pylint:disable=too-many-instance-attributes
    """
    Holds the Collection metadata.

    Attributes:
        category: The category of the dataset.
        region: The region the dataset is from.
        gsd: The Ground Sample Distance of the dataset.
        start_datetime: The start datetime of the dataset.
        end_datetime: The end datetime of the dataset.
        lifecycle: The lifecycle of the dataset.
        linz_slug: The LINZ slug of the dataset.
        collection_id: The collection ID.
        geographic_description: The geographic description of the dataset.
        event_name: The event name of the dataset.
        historic_survey_number: The historic survey number of the dataset.
    """

    category: str
    region: str
    gsd: Decimal
    start_datetime: datetime
    end_datetime: datetime
    lifecycle: str
    linz_slug: str
    collection_id: str | None = None
    geographic_description: str | None = None
    event_name: str | None = None
    historic_survey_number: str | None = None


class SubtypeParameterError(Exception):
    def __init__(self, category: str) -> None:
        self.message = f"Unrecognised/Unimplemented Subtype Parameter: {category}"


class MissingMetadataError(Exception):
    def __init__(self, metadata: str) -> None:
        self.message = f"Missing metadata: {metadata}"


AERIAL_PHOTOS = "aerial-photos"
SCANNED_AERIAL_PHOTOS = "scanned-aerial-photos"
RURAL_AERIAL_PHOTOS = "rural-aerial-photos"
SATELLITE_IMAGERY = "satellite-imagery"
URBAN_AERIAL_PHOTOS = "urban-aerial-photos"
DEM = "dem"
DSM = "dsm"
DEM_HILLSHADE = "dem-hillshade"
DEM_HILLSHADE_IGOR = "dem-hillshade-igor"

DATA_CATEGORIES = {
    AERIAL_PHOTOS: "Aerial Photos",
    SCANNED_AERIAL_PHOTOS: "Scanned Aerial Photos",
    RURAL_AERIAL_PHOTOS: "Rural Aerial Photos",
    SATELLITE_IMAGERY: "Satellite Imagery",
    URBAN_AERIAL_PHOTOS: "Urban Aerial Photos",
    DEM: "DEM",
    DSM: "DSM",
    DEM_HILLSHADE: "DEM Hillshade",
    DEM_HILLSHADE_IGOR: "DEM Hillshade Igor",
}

HUMAN_READABLE_REGIONS = {
    "antarctica": "Antarctica",
    "auckland": "Auckland",
    "bay-of-plenty": "Bay of Plenty",
    "canterbury": "Canterbury",
    "gisborne": "Gisborne",
    "global": "Global",
    "hawkes-bay": "Hawke's Bay",
    "manawatu-whanganui": "Manawatū-Whanganui",
    "marlborough": "Marlborough",
    "nelson": "Nelson",
    "new-zealand": "New Zealand",
    "northland": "Northland",
    "otago": "Otago",
    "pacific-islands": "Pacific Islands",
    "southland": "Southland",
    "taranaki": "Taranaki",
    "tasman": "Tasman",
    "waikato": "Waikato",
    "wellington": "Wellington",
    "west-coast": "West Coast",
}

LIFECYCLE_SUFFIXES = {
    "preview": "- Preview",
    "ongoing": "- Draft",
}
