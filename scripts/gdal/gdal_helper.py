import os
import subprocess
from enum import Enum
from typing import List, Optional

from linz_logger import get_log

from scripts.aws.aws_helper import get_session_credentials, is_s3
from scripts.logging.time_helper import time_in_ms


class GDALExecutionException(Exception):
    pass


class EpsgCode(str, Enum):
    EPSG_2193 = "EPSG:2193"
    """ NZGD2000 / New Zealand Transverse Mercator 2000 (NZTM) """
    EPSG_4326 = "EPSG:4326"
    """ WGS84 - World Geodetic System 1984"""


def get_vfs_path(path: str) -> str:
    """Make the path as a GDAL Virtual File Systems path.

    Args:
        path (str): a path to a file.

    Returns:
        str: the path modified to comply with the corresponding storage service.
    """
    return path.replace("s3://", "/vsis3/")


def command_to_string(command: List[str]) -> str:
    """Format the command, each arguments separated by a white space.

    Args:
        command (List[str]): each arguments of the command as a string in a list.

    Returns:
        str: the formatted command.
    """
    return " ".join(command)


def get_gdal_version() -> str:
    """Return the GDAL version assuming all GDAL commands are in the same version of gdalinfo.

    Raises:
        GDALExecutionException: If the GDAL command fails.

    Returns:
        str: The GDAL version returned by GDAL.
    """
    gdal_env = os.environ.copy()
    gdalinfo_version = ["gdalinfo", "--version"]
    try:
        proc = subprocess.run(gdalinfo_version, env=gdal_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return proc.stdout.decode().strip()
    except subprocess.CalledProcessError as cpe:
        get_log().error("get_gdal_version_failed", command=command_to_string(gdalinfo_version), error=str(cpe.stderr, "utf-8"))
        raise GDALExecutionException(f"GDAL {str(cpe.stderr, 'utf-8')}") from cpe


def run_gdal(
    command: List[str],
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
) -> "subprocess.CompletedProcess[bytes]":
    """Run the GDAL command. The permissions to access to the input file are applied to the gdal environment.

    Args:
        command: each arguments of the GDAL command
        input_file: the input file path
        output_file: the output file path

    Raises:
        cpe: CalledProcessError is raised if something goes wrong during the execution of the command

    Returns:
        subprocess.CompletedProcess: the output process.
    """
    gdal_env = os.environ.copy()
    temp_command = command.copy()

    if input_file:
        if is_s3(input_file):
            # Set the credentials for GDAL to be able to read the input file
            credentials = get_session_credentials(input_file)
            gdal_env["AWS_ACCESS_KEY_ID"] = credentials.access_key
            gdal_env["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
            gdal_env["AWS_SESSION_TOKEN"] = credentials.token
            input_file = get_vfs_path(input_file)
        temp_command.append(input_file)

    if output_file:
        temp_command.append(output_file)

    start_time = time_in_ms()
    try:
        get_log().debug("run_gdal_start", command=command_to_string(temp_command))
        proc = subprocess.run(temp_command, env=gdal_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as cpe:
        get_log().error("run_gdal_failed", command=command_to_string(temp_command), error=str(cpe.stderr, "utf-8"))
        raise GDALExecutionException(f"GDAL {str(cpe.stderr, 'utf-8')}") from cpe
    finally:
        get_log().info("run_gdal_end", command=command_to_string(temp_command), duration=time_in_ms() - start_time)

    if proc.stderr:
        get_log().warning("run_gdal_stderr", command=command_to_string(temp_command), stderr=proc.stderr.decode())

    get_log().trace("run_gdal_succeeded", command=command_to_string(temp_command), stdout=proc.stdout.decode())

    return proc


def get_srs() -> bytes:
    """Run `gdalsrsinfo` with the EPSG code `2193`

    Raises:
        Exception: if `gdal` has an stderr

    Returns:
        the output of `gdalsrsinfo`
    """
    gdalsrsinfo_command = ["gdalsrsinfo", "-o", "wkt", EpsgCode.EPSG_2193]
    gdalsrsinfo_result = run_gdal(gdalsrsinfo_command)
    if gdalsrsinfo_result.stderr:
        raise Exception(
            f"Error trying to retrieve srs from epsg code, no files have been checked\n{gdalsrsinfo_result.stderr!r}"
        )
    return gdalsrsinfo_result.stdout
