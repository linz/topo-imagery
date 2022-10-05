import json
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
            get_log().error("Gdalinfo_error", file=path, error=str(gdalinfo_process.stderr))
            if file_check:
                file_check.add_error(error_type="gdalinfo", error_message=f"error(s): {str(gdalinfo_process.stderr)}")
            else:
                raise Exception(f"Gdalinfo Error {str(gdalinfo_process.stderr)}")
        return gdalinfo_result
    except GDALExecutionException as gee:
        get_log().error("gdalinfo_failed", file=path, error=str(gee))
        if file_check:
            file_check.add_error(error_type="gdalinfo", error_message=f"failed: {str(gee)}")
            return gdalinfo_result
        raise gee
