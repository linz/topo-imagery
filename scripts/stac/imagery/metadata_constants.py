from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict


class CollectionMetadata(TypedDict):
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
    geographic_description: Optional[str]


class SubtypeParameterError(Exception):
    def __init__(self, category: str) -> None:
        self.message = f"Unrecognised/Unimplemented Subtype Parameter: {category}"

@dataclass
class Category():
    id: str
    name: str

class ElevationCategories(Enum):
    DEM = ("dem", "DEM")
    DSM = ("dsm", "DSM")
    def __init__(self, _id: str, name: str) -> None:
        self.id = _id
        self.name = name
             
class ImageryCategories(str, Enum):
    AERIAL = "Aerial Photos"
    HISTORICAL = "Scanned Aerial Photos"
    RURAL = "Rural Aerial Photos"
    SATELLITE = "Satellite Imagery"
    URBAN = "Urban Aerial Photos"

ELEVATION_CATEGORIES_IDS = {
    ElevationCategories.DEM.value: "dem",
    ElevationCategories.DSM.value: "dsm"
}

IMAGERY_CATEGORIES_IDS = {
    ImageryCategories.AERIAL.value:"aerial-photos",
    ImageryCategories.HISTORICAL.value:"scanned-aerial-photos",
    ImageryCategories.RURAL.value:"rural-aerial-photos",
    ImageryCategories.SATELLITE.value: "satellite-imagery",
    ImageryCategories.URBAN.value: "urban-aerial-photos"
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
