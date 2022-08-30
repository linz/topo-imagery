import json
from typing import Any, Dict

from linz_logger import get_log

from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal


def gdal_info(path: str) -> Dict[Any, Any]:
    gdalinfo_command = ["gdalinfo", "-stats", "-json", "--config", "GDAL_PAM_ENABLED", "NO"]
    try:
        gdalinfo_process = run_gdal(gdalinfo_command, path)
        gdalinfo_result = {}
        try:
            gdalinfo_result = json.loads(gdalinfo_process.stdout)
        except json.JSONDecodeError as e:
            get_log().error("load_gdalinfo_result_error", file=path, error=e)
            raise e
        if gdalinfo_process.stderr:
            get_log().error("Gdalinfo_error", file=path, error=str(gdalinfo_process.stderr))
            raise Exception(f"Gdalinfo Error {str(gdalinfo_process.stderr)}")
        return gdalinfo_result
    except GDALExecutionException as gee:
        get_log().error("gdalinfo_failed", file=path, error=str(gee))
        raise gee
