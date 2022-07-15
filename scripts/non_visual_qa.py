import argparse
import json
from typing import Any, Dict, List, Optional

from format_source import format_source
from gdal_helper import GDALExecutionException, run_gdal
from linz_logger import get_log


class NonVisualQA:
    def __init__(self) -> None:
        self.errors: List[Dict[str, Any]] = []
        self._valid = True

    def add_error(self, type: str, description: str, custom_fields: Dict[str, str] = {}) -> None:
        self.errors.append({"type": type, "description": description, custom_fields})
        self._valid = False

    def is_valid(self) -> bool:
        return self._valid


def check_no_data(gdalinfo: Dict[str, Any], file_errors: Dict[str, str]) -> None:
    """Add an error in errors_list if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands".

    Args:
        gdalinfo (Dict[str, Any]): JSON return of gdalinfo in a Python Dictionary.
        errors_list (List[str]): List of errors as strings.
    """
    bands = gdalinfo["bands"]
    if "noDataValue" in bands[0]:
        current_nodata_val = bands[0]["noDataValue"]
        if current_nodata_val != 255:
            file_errors["no_data"] = f"noDataValue is {int(current_nodata_val)} not 255"
    else:
        file_errors["no_data"] = "noDataValue not set"


def check_band_count(gdalinfo: Dict[str, Any], file_errors: Dict[str, str]) -> None:
    """Add an error in errors_list if there is no exactly 3 bands found.

    Args:
        gdalinfo (Dict[str, Any]): JSON returned by gdalinfo as a Python Dictionary.
        errors_list (List[str]): List of errors as strings.
    """
    bands = gdalinfo["bands"]
    bands_num = len(bands)
    if bands_num != 3:
        file_errors["band_count"] = f"not 3 bands, {bands_num} bands found"


def check_srs(gdalsrsinfo: bytes, gdalsrsinfo_tif: bytes, file_errors: Dict[str, str]) -> None:
    """Add an error in errors_list if gdalsrsinfo and gdalsrsinfo_tif values are different.

    Args:
        gdalsrsinfo (str): Value returned by gdalsrsinfo as a string.
        gdalsrsinfo_tif (str): Value returned by gdalsrsinfo for the tif as a string.
        errors_list (List[str]): List of errors as strings.
    """
    if gdalsrsinfo_tif != gdalsrsinfo:
        file_errors["srs"] = "different srs"


def check_color_interpretation(gdalinfo: Dict[str, Any], file_errors: Dict[str, str]) -> None:
    bands = gdalinfo["bands"]
    missing_bands = []
    band_colour_ints = {1: "Red", 2: "Green", 3: "Blue"}
    n = 1
    for band in bands:
        colour_int = band["colorInterpretation"]
        if n in band_colour_ints:
            if colour_int != band_colour_ints[n]:
                missing_bands.append(f"band {n} {colour_int}")
        else:
            missing_bands.append(f"band {n} {colour_int}")
        n += 1
    if missing_bands:
        missing_bands.sort()
        file_errors["color_interpretation"] = f"unexpected color interpretation bands; {', '.join(missing_bands)}"


def main() -> None:  # pylint: disable=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser.parse_args()
    source = arguments.source

    source = format_source(source)

    # Get srs
    gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", "EPSG:2193"]
    gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
    if gdalsrsinfo_result.stderr:
        raise Exception(
            f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr!r}"
        )
    srs = gdalsrsinfo_result.stdout

    errors_report = {}
    for file in source:
        gdalinfo_command = ["gdalinfo", "-stats", "-json"]
        try:
            gdalinfo_process = run_gdal(gdalinfo_command, file)
            gdalinfo_result = {}
            try:
                gdalinfo_result = json.loads(gdalinfo_process.stdout)
            except json.JSONDecodeError as e:
                get_log().error("load_gdalinfo_result_error", file=file, error=e)
                gdalinfo_errors = f"GDALINFO RESULT ISSUE: {str(e)}"
                continue
            gdalinfo_errors = str(gdalinfo_process.stderr)
        except GDALExecutionException as gee:
            gdalinfo_errors = f"GDALINFO FAILED: {str(gee)}"
            continue

        # Check result
        errors: Dict[str, str] = {}
        # No data
        check_no_data(gdalinfo_result, errors)

        # Band count
        check_band_count(gdalinfo_result, errors)

        # srs
        gdalsrsinfo_tif_command = ["gdalsrsinfo", "-o", "wkt"]
        try:
            gdalsrsinfo_tif_result = run_gdal(gdalsrsinfo_tif_command, file)
            check_srs(srs, gdalsrsinfo_tif_result.stdout, errors)
        except GDALExecutionException as gee:
            errors["srs"] = f"NOT CHECKED: {str(gee)}"

        # Color interpretation
        check_color_interpretation(gdalinfo_result, errors)

        # gdal errors
        if gdalinfo_errors:
            errors["gdal"] = f"{gdalinfo_errors!r}"

        if errors:
            errors_report[file] = errors

    if errors_report:
        get_log().info("non_visual_qa_errors", errors=errors_report)
    else:
        get_log().info("non_visual_qa_no_error")


if __name__ == "__main__":
    main()
