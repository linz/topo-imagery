import json
import re
from typing import Any, Dict, List, Optional, TypedDict, cast

from linz_logger import get_log

from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal
from scripts.tile.tile_index import Point


class GdalInfoBand(TypedDict):
    band: int
    """band offset, starting at 1
    """
    block: List[int]
    type: str
    colorInterpretation: str
    """Color
    Examples:
        "Red", "Green", "Blue", "Alpha", "Gray"
    """
    noDataValue: Optional[int]


class GdalInfo(TypedDict):
    description: str
    """Information about the target of the gdalinfo
    """
    driverShortName: str
    """Short names for the driver

    Example: "GTiff"

    """
    driverLongName: str
    """Longer driver name

    Example:
        "GeoTIFF"
    """

    files: List[str]
    """List of files processed by the command
    """
    size: List[int]
    """Width and height of input"""
    geoTransform: List[float]
    """GeoTransformation information

    """
    metadata: Dict[Any, Any]
    cornerCoordinates: Dict[Any, Any]
    extent: Dict[Any, Any]
    wgs84Extent: Optional[Dict[str, List[float]]]
    bands: List[GdalInfoBand]


def gdal_info(path: str, stats: bool = True) -> GdalInfo:
    """run gdalinfo on the provided file

    Args:
        path: path to file to gdalinfo
        stats: Optionally add "-stats" to gdalinfo. Defaults to True.

    Returns:
        GdalInfo output
    """
    # Set GDAL_PAM_ENABLED to NO to temporarily diable PAM support and prevent creation of auxiliary XML file.
    gdalinfo_command = ["gdalinfo", "-json", "--config", "GDAL_PAM_ENABLED", "NO"]

    # Stats takes a while to generate only generate if needed
    if stats:
        gdalinfo_command.append("-stats")

    try:
        gdalinfo_process = run_gdal(gdalinfo_command, path)
        return cast(GdalInfo, json.loads(gdalinfo_process.stdout))
    except json.JSONDecodeError as e:
        get_log().error("load_gdalinfo_result_error", file=path, error=e)
        raise e
    except GDALExecutionException as e:
        get_log().error("gdalinfo_failed", file=path, error=str(e))
        raise e


def format_wkt(wkt: str) -> str:
    """Remove newline, spaces, and replace double quotes by quotes in wkt output (gdalinfo).

    Args:
        wkt (str): The wkt output from gdalinfo.

    Returns:
        str: The wkt output formatted.
    """
    return re.sub(r"\s+", " ", (wkt.replace('"', "'").replace("\n", "")))


def get_origin(gdalinfo: GdalInfo) -> Point:
    return Point(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])
