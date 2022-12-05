import json
import re
from typing import Any, Dict, List, Optional, TypedDict, cast

from linz_logger import get_log

from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal


class GdalInfoBand(TypedDict):
    band: int
    block: List[int]
    type: str
    colorInterpretation: str
    noDataValue: Optional[int]


class GdalInfo(TypedDict):
    description: str
    driverShortName: str
    driverLongName: str
    files: List[str]
    size: List[int]
    geoTransform: List[float]
    metadata: Dict[Any, Any]
    cornerCoordinates: Dict[Any, Any]
    extent: Dict[Any, Any]
    wgs84Extent: Optional[Dict[str, List[float]]]
    bands: List[GdalInfoBand]


def gdal_info(path: str, stats: bool = True) -> GdalInfo:
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
