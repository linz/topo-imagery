import string
from datetime import datetime
from enum import Enum
from typing import Optional


class SubtypeParameterError(Exception):
    def __init__(self, subtype: str) -> None:
        self.message = f"Unrecognised/Unimplemented Subtype Parameter: {subtype}"


class ImagerySubtypes(str, Enum):
    SATELLIE = "Satellite Imagery"
    URBAN = "Urban Aerial Photos"
    RURAL = "Rural Aerial Photos"
    AERIAL = "Aerial Photos"
    HISTORICAL = "Scanned Aerial Photos"


class ElevationSubtypes(str, Enum):
    DEM = "DEM"
    DSM = "DSM"


def generate_title(
    subtype: str,
    region: str,
    gsd: str,
    start_datetime: datetime,
    end_datetime: datetime,
    lifecycle: str,
    location: Optional[str] = None,
    event: Optional[str] = None,
    historic_survey_number: Optional[str] = None,
) -> str:
    """Generates the title for imagery and elevation datasets.
    Satellite Imagery / Urban Aerial Photos / Rural Aerial Photos:
    [Location Name / Region if no Location Name specified] [GSD] [?Event Name] [Data Sub-Type] ([Year(s)]) [?- Preview]
    DEM / DSM:
    [Location Name / Region if no Location Name specified] [?- Event Name] LiDAR [GSD] [Data Sub-Type] ([Year(s)]) [?- Preview]
    If Historic Survey Number:
    [Location Name / Region if no Location Name specified] [GSD] [Survey Number] ([Year(s)]) [?- Preview]

    Args:
        subtype: Dataset subtype description - used to determine if the dataset is imagery, elevation, ect.
        region: Region of Dataset
        gsd: Dataset Ground Sample Distance
        start_date: Dataset capture start date
        end_date: Dataset capture end date
        lifecycle: Dataset status
        location: Optional location of dataset, e.g.- Hutt City
        event: Optional details of capture event, e.g. - Cyclone Gabreille
        historic_survey_number: Optional historic imagery survey number, e.g.- SNC88445
    Returns:
        Dataset Title
    """
    # pylint: disable-msg=too-many-arguments

    date = _format_date_for_metadata(start_datetime, end_datetime)
    name = _format_name_for_title(_region_map(region), location)
    preview = _is_preview(lifecycle)

    if historic_survey_number:
        return " ".join(f"{name} {gsd} {historic_survey_number} ({date}) {preview or ''}".split())

    if subtype in [ImagerySubtypes.SATELLIE, ImagerySubtypes.URBAN, ImagerySubtypes.RURAL]:
        return " ".join(f"{name} {gsd} {event or ''} {subtype} ({date}) {preview or ''}".split())
    if subtype in [ElevationSubtypes.DEM, ElevationSubtypes.DSM]:
        return " ".join(
            f"{name} {_format_event_for_elevation_title(event) or ''} LiDAR {gsd} {subtype} ({date}) {preview or ''}".split()
        )

    raise SubtypeParameterError(subtype)


def generate_description(
    subtype: str,
    region: str,
    start_date: datetime,
    end_date: datetime,
    location: Optional[str] = None,
    event: Optional[str] = None,
    historic_survey_number: Optional[str] = None,
) -> str:
    """Generates the descriptions for imagery and elevation datasets.
    Urban Aerial Photos / Rural Aerial Photos:
    Orthophotography within the [Region] region captured in the [Year(s)] flying season.
    DEM / DSM:
    [Digital Surface Model / Digital Elevation Model] within the [region] [?- location] region in [year(s)].
    Satellite Imagery:
    Satellite imagery within the [Region] region captured in [Year(s)].
    Historical Imagery:
    Scanned aerial imagery within the [Region] region captured in [Year(s)].

    Args:
        subtype: Dataset subtype description - used to determine if the dataset is imagery, elevation, ect.
        region: Region of Dataset
        start_date: Dataset capture start date
        end_date: Dataset capture end date
        location: Optional location of dataset, e.g.- Hutt City
        event: Optional details of capture event, e.g. - Cyclone Gabreille
        historic_survey_number: Optional historic imagery survey number, e.g.- SNC88445

    Returns:
        Dataset Description
    """
    date = _format_date_for_metadata(start_date, end_date)
    location_txt = _format_location_for_elevation_description(location)  # TODO: rename
    region = _region_map(region)
    desc = None

    if historic_survey_number:
        desc = f"Scanned aerial imagery within the {region} region captured in {date}."

    if subtype == ImagerySubtypes.SATELLIE:
        desc = f"Satellite imagery within the {region} region captured in {date}."
    elif subtype in [ImagerySubtypes.URBAN, ImagerySubtypes.RURAL]:
        desc = f"Orthophotography within the {region} region captured in the {date} flying season."
    elif subtype == ElevationSubtypes.DEM:
        desc = " ".join(f"Digital Elevation Model within the {region} {location_txt or ''} region in {date}.".split())
    elif subtype == ElevationSubtypes.DSM:
        desc = " ".join(f"Digital Surface Model within the {region} {location_txt or ''} region in {date}.".split())

    if not desc:
        raise SubtypeParameterError(subtype)
    if event:
        desc = desc.replace(".", f", published as a record of the {event} event.")

    return desc


def _format_date_for_metadata(start_date: datetime, end_date: datetime) -> str:
    if start_date.year == end_date.year:
        return str(start_date.year)
    return f"{start_date.year} - {end_date.year}"


def _format_name_for_title(region: str, location: Optional[str]) -> str:
    if location:
        return location
    return region


def _is_preview(lifecycle: str) -> Optional[str]:
    """lifeycle is only added to a dataset title if the status is preview."""
    if lifecycle == "preview":
        return "- preview"
    return None


def _format_location_for_elevation_description(location: Optional[str]) -> Optional[str]:
    if location:
        return f"- {location}"
    return None


def _format_event_for_elevation_title(event: Optional[str]) -> Optional[str]:
    if event:
        return f"- {event}"
    return None


def _region_map(region: str) -> str:
    """Convert region parameters from ascii input to uft-8"""
    if region == "hawkes-bay":
        return "Hawke's Bay"
    if region == "manawatu-whanganui":
        return "Manawatū-Whanganui"
    return string.capwords(region.replace("-", " "))
