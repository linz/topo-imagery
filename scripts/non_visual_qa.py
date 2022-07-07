import argparse
import subprocess
import tempfile

from file_helper import get_file_name_from_path
from gdal_helper import run_gdal
from linz_logger import get_log

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source", required=True)
# parser.add_argument("--destination", dest="destination", required=True)
arguments = parser.parse_args()
source = arguments.source
# destination = arguments.destination


def get_srs_from_epsg(epsg):
    command = ["gdalsrsinfo", "-o", "wkt", f"EPSG:{epsg}"]
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as cpe:
        get_log().error("run_gdal_translate_failed", command=" ".join(command))
        raise cpe
    if proc.stderr:
        raise Exception(f"Error trying to retrieve srs from epsg code, no files have been checked\n{proc.stderr}")
    return proc.stdout


print(get_srs_from_epsg(2193))

command = ["gdalinfo", "-stats", "-json"]
process = run_gdal(command, source)

# Write results
tif_filename = get_file_name_from_path(source)
stdout_filename = f"{tif_filename}_stdout.json"
sterr_filename = f"{tif_filename}_stderr.json"
with tempfile.TemporaryDirectory() as tmp_dir:
    with open(stdout_filename, "w", encoding="UTF-8") as file:
        get_log("stdout", stdout=process.stdout)
        file.write(process.stdout)
    with open(sterr_filename, "w", encoding="UTF-8") as file:
        file.write(process.stdout)
        get_log("stderr", stdout=process.stderr)
