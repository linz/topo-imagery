import argparse
import json

from gdal_helper import run_gdal
from linz_logger import get_log

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source", required=True)
arguments = parser.parse_args()
source = arguments.source

# Get srs
gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", "EPSG:2193"]
gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
if gdalsrsinfo_result.stderr:
    raise Exception(f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr}")
srs = gdalsrsinfo_result.stdout

gdalinfo_command = ["gdalinfo", "-stats", "-json"]
gdalinfo_process = run_gdal(gdalinfo_command, source)
gdalinfo_result = {}
try:
    gdalinfo_result = json.loads(gdalinfo_process.stdout)
except json.JSONDecodeError as e:
    get_log().error("load_gdalinfo_result_error", error=e)
    # TODO change this behavior when loop over multiple TIFF files to go to next file instead of raising the exception
    raise e
gdalinfo_errors = gdalinfo_process.stderr

# Check result
errors = []
# No data
current_bands = gdalinfo_result["bands"]
if "noDataValue" in current_bands[0]:
    current_nodata_val = current_bands[0]["noDataValue"]
    if current_nodata_val != 255:
        errors.append(f"noDataValue is {int(current_nodata_val)} not 255")
else:
    errors.append("noDataValue not set")

# Band count
current_bands = gdalinfo_result["bands"]
current_band_num = len(current_bands)
if current_band_num != 3:
    errors.append(f"not 3 bands, {current_band_num} bands found")

# srs
gdalsrsinfo_tiff_command = ["gdalsrsinfo", "-o", "wkt"]
gdalsrsinfo_tiff_result = run_gdal(gdalsrsinfo_command, source)
if gdalsrsinfo_tiff_result.stdout != srs:
    errors.append("different srs")

# Color interpretation
current_bands = gdalinfo_result["bands"]
missing_bands = []
band_colour_ints = {1: "Red", 2: "Green", 3: "Blue"}
for n in range(len(current_bands)):
    colour_int = current_bands[n]["colorInterpretation"]
    if n + 1 in band_colour_ints:
        if colour_int != band_colour_ints[n + 1]:
            missing_bands.append(f"band {n+1} {colour_int}")
    else:
        missing_bands.append(f"band {n+1} {colour_int}")
if missing_bands:
    missing_bands.sort()
    errors.append(f"unexpected color interpretation bands; {', '.join(missing_bands)}")

# gdal errors
errors.append(gdalinfo_errors)

get_log().info("non_visual_qa_result", result=errors)
