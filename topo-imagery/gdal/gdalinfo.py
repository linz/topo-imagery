import json
import re
from typing import Any, Dict, List, Optional, TypedDict, cast

from linz_logger import get_log

from topo-imagery.gdal.gdal_helper import GDALExecutionException, run_gdal
from topo-imagery.tile.tile_index import Point


class GdalInfoBandColorTable(TypedDict):
    palette: str
    """Colour palette type
    Example: "RGB" """
    count: int
    """Count of entries in the colour palette
    Example: 256"""
    entries: List[List[int]]
    """List of colour palette entries. Each is a list of colour channel values
    Example:
    [
        [255,255,255,255],
        [254,254,254,255],
        [253,253,253,255],
        [252,252,252,255],
        [251,251,251,255],
        [250,250,250,255]
        ...
    ]"""


class GdalInfoBand(TypedDict):
    band: int
    """band offset, starting at 1
    """
    block: List[int]
    type: str
    colorInterpretation: str
    """Color
    Examples:
        "Red", "Green", "Blue", "Alpha", "Gray", "Palette"
    """
    noDataValue: Optional[int]
    colorTable: Optional[GdalInfoBandColorTable]


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


def gdal_info(path: str) -> GdalInfo:
    """run gdalinfo on the provided file

    Args:
        path: path to file to gdalinfo

    Returns:
        GdalInfo output
    """
    # Set GDAL_PAM_ENABLED to NO to temporarily diable PAM support and prevent creation of auxiliary XML file.
    gdalinfo_command = ["gdalinfo", "-json", "--config", "GDAL_PAM_ENABLED", "NO"]

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
    """Parse the `GdalInfo` to get the origin coordinates.

    Args:
        gdalinfo: the output of gdalinfo

    Returns:
        a `Point` of the origin
    """
    return Point(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])
