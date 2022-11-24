import json
import re
from typing import Any, Dict

from linz_logger import get_log

from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal


def gdal_info(path: str) -> Dict[Any, Any]:
    # Set GDAL_PAM_ENABLED to NO to temporarily diable PAM support and prevent creation of auxiliary XML file.
    gdalinfo_command = ["gdalinfo", "-stats", "-json", "--config", "GDAL_PAM_ENABLED", "NO"]
    gdalinfo_result = {}
    try:
        gdalinfo_process = run_gdal(gdalinfo_command, path)
        try:
            gdalinfo_result = json.loads(gdalinfo_process.stdout)
        except json.JSONDecodeError as e:
            get_log().error("load_gdalinfo_result_error", file=path, error=e)
            raise e
        return gdalinfo_result
    except GDALExecutionException as gee:
        get_log().error("gdalinfo_failed", file=path, error=str(gee))
        raise gee


def format_wkt(wkt: str) -> str:
    """Remove newline, spaces, and replace double quotes by quotes in wkt output (gdalinfo).

    Args:
        wkt (str): The wkt output from gdalinfo.

    Returns:
        str: The wkt output formatted.
    """
    return re.sub(r"\s+", " ", (wkt.replace('"', "'").replace("\n", "")))
