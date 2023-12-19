from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict


class CollectionTitleMetadata(TypedDict):
    """
    region: Region of Dataset
    gsd: Dataset Ground Sample Distance
    start_date: Dataset capture start date
    end_date: Dataset capture end date
    lifecycle: Dataset status
    Optional:
        location: Optional location of dataset, e.g. Hutt City
        event: Optional details of capture event, e.g. Cyclone Gabrielle
        historic_survey_number: Optional historic imagery survey number, e.g. SNC88445
    """

    category: str
    region: str
    gsd: str
    start_datetime: datetime
    end_datetime: datetime
    lifecycle: str
    location: Optional[str]
    event: Optional[str]
    historic_survey_number: Optional[str]


class SubtypeParameterError(Exception):
    def __init__(self, category: str) -> None:
        self.message = f"Unrecognised/Unimplemented Subtype Parameter: {category}"


class ImageryCategories(str, Enum):
    SATELLITE = "Satellite Imagery"
    URBAN = "Urban Aerial Photos"
    RURAL = "Rural Aerial Photos"
    AERIAL = "Aerial Photos"
    HISTORICAL = "Scanned Aerial Photos"


class ElevationCategories(str, Enum):
    DEM = "DEM"
    DSM = "DSM"


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
