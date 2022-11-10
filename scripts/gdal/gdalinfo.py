import json
import re
from typing import Any, Dict, Optional

from linz_logger import get_log

from scripts.files.file_check import FileCheck
from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal


def gdal_info(path: str, file_check: Optional[FileCheck] = None) -> Dict[Any, Any]:
    # Set GDAL_PAM_ENABLED to NO to temporarily diable PAM support and prevent creation of auxiliary XML file.
    gdalinfo_command = ["gdalinfo", "-stats", "-json", "--config", "GDAL_PAM_ENABLED", "NO"]
    gdalinfo_result = {}
    try:
        gdalinfo_process = run_gdal(gdalinfo_command, path)
        try:
            gdalinfo_result = json.loads(gdalinfo_process.stdout)
        except json.JSONDecodeError as e:
            get_log().error("load_gdalinfo_result_error", file=path, error=e)
            if file_check:
                file_check.add_error(error_type="gdalinfo", error_message=f"parsing result issue: {str(e)}")
            else:
                raise e
        if gdalinfo_process.stderr:
            if file_check:
                # FIXME: do we want this recorded as an error in the non_visual_qa report?
                file_check.add_error(error_type="gdalinfo", error_message=f"error(s): {str(gdalinfo_process.stderr)}")
        return gdalinfo_result
    except GDALExecutionException as gee:
        get_log().error("gdalinfo_failed", file=path, error=str(gee))
        if file_check:
            file_check.add_error(error_type="gdalinfo", error_message=f"failed: {str(gee)}")
            return gdalinfo_result
        raise gee


def format_wkt(wkt: str) -> str:
    """Remove special characters and replace double quotes by quotes in wkt output (gdalinfo).

    Args:
        wkt (str): The wkt output from gdalinfo.

    Returns:
        str: The wkt output formatted.
    """
    return re.sub(r"\s+", " ", (wkt.replace('"', "'").replace("\n", "")))
