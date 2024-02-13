from datetime import datetime
from typing import Optional, TypedDict


class CollectionMetadata(TypedDict):
    """
    Used to generate dataset collection titles and descriptions.

    region: Region of Dataset
    gsd: Dataset Ground Sample Distance
    start_date: Dataset capture start date
    end_date: Dataset capture end date
    lifecycle: Dataset status
    Optional:
        geographic_description: Optional geographic_description of dataset, e.g. Hutt City
        event: Optional details of capture event, e.g. Cyclone Gabrielle
        historic_survey_number: Optional historic imagery survey number, e.g. SNC88445
    """

    category: str
    region: str
    gsd: str
    start_datetime: datetime
    end_datetime: datetime
    lifecycle: str
    geographic_description: Optional[str]
    event_name: Optional[str]
    historic_survey_number: Optional[str]


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

DATA_CATEGORIES = {
    AERIAL_PHOTOS: "Aerial Photos",
    SCANNED_AERIAL_PHOTOS: "Scanned Aerial Photos",
    RURAL_AERIAL_PHOTOS: "Rural Aerial Photos",
    SATELLITE_IMAGERY: "Satellite Imagery",
    URBAN_AERIAL_PHOTOS: "Urban Aerial Photos",
    DEM: "DEM",
    DSM: "DSM",
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
