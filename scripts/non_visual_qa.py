import argparse
import json
from typing import Any, Dict, List

from format_source import format_source
from gdal_helper import run_gdal
from linz_logger import get_log


def check_no_data(gdalinfo: Dict[str, Any], errors_list: List[str]) -> None:
    """Add an error in errors_list if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands".

    Args:
        gdalinfo (Dict[str, Any]): JSON return of gdalinfo in a Python Dictionary.
        errors_list (List[str]): List of errors as strings.
    """
    bands = gdalinfo["bands"]
    if "noDataValue" in bands[0]:
        current_nodata_val = bands[0]["noDataValue"]
        if current_nodata_val != 255:
            errors_list.append(f"noDataValue is {int(current_nodata_val)} not 255")
    else:
        errors_list.append("noDataValue not set")


def check_band_count(gdalinfo: Dict[str, Any], errors_list: List[str]) -> None:
    """Add an error in errors_list if there is no exactly 3 bands found.

    Args:
        gdalinfo (Dict[str, Any]): JSON returned by gdalinfo as a Python Dictionary.
        errors_list (List[str]): List of errors as strings.
    """
    bands = gdalinfo["bands"]
    bands_num = len(bands)
    if bands_num != 3:
        errors_list.append(f"not 3 bands, {bands_num} bands found")


def check_srs(gdalsrsinfo: bytes, gdalsrsinfo_tif: bytes, errors_list: List[str]) -> None:
    """Add an error in errors_list if gdalsrsinfo and gdalsrsinfo_tif values are different.

    Args:
        gdalsrsinfo (str): Value returned by gdalsrsinfo as a string.
        gdalsrsinfo_tif (str): Value returned by gdalsrsinfo for the tif as a string.
        errors_list (List[str]): List of errors as strings.
    """
    if gdalsrsinfo_tif != gdalsrsinfo:
        errors_list.append("different srs")


def check_color_interpretation(gdalinfo: Dict[str, Any], errors_list: List[str]) -> None:
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
        errors_list.append(f"unexpected color interpretation bands; {', '.join(missing_bands)}")


def main() -> None:
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

    for file in source:
        gdalinfo_command = ["gdalinfo", "-stats", "-json"]
        gdalinfo_process = run_gdal(gdalinfo_command, file)
        gdalinfo_result = {}
        try:
            gdalinfo_result = json.loads(gdalinfo_process.stdout)
        except json.JSONDecodeError as e:
            get_log().error("load_gdalinfo_result_error", file=file, error=e)
            continue

        gdalinfo_errors = gdalinfo_process.stderr

        # Check result
        errors: List[str] = []
        # No data
        check_no_data(gdalinfo_result, errors)

        # Band count
        check_band_count(gdalinfo_result, errors)

        # srs
        gdalsrsinfo_tif_command = ["gdalsrsinfo", "-o", "wkt"]
        gdalsrsinfo_tif_result = run_gdal(gdalsrsinfo_tif_command, file)
        check_srs(srs, gdalsrsinfo_tif_result.stdout, errors)

        # Color interpretation
        check_color_interpretation(gdalinfo_result, errors)

        # gdal errors
        errors.append(f"{gdalinfo_errors!r}")

        if len(errors) > 0:
            get_log().info("non_visual_qa_errors_found", file=file, result=errors)
        else:
            get_log().info("non_visual_qa_no_error", file=file)


if __name__ == "__main__":
    main()
