import json
import os
import subprocess
from typing import List, Optional

from linz_logger import get_log

from scripts.aws.aws_helper import get_bucket_name_from_path, get_credentials, is_s3
from scripts.logging.time_helper import time_in_ms


class GDALExecutionException(Exception):
    pass


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


def run_gdal(
    command: List[str],
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
) -> "subprocess.CompletedProcess[bytes]":
    """Run the GDAL command. The permissions to access to the input file are applied to the gdal environment.

    Args:
        command (List[str]): each arguments of the GDAL command.
        input_file (str, optional): the input file path.
        output_file (str, optional): the output file path.

    Raises:
        cpe: CalledProcessError is raised if something goes wrong during the execution of the command.

    Returns:
        subprocess.CompletedProcess: the output process.
    """
    gdal_env = os.environ.copy()

    if input_file:
        if is_s3(input_file):
            # Set the credentials for GDAL to be able to read the input file
            credentials = get_credentials(get_bucket_name_from_path(input_file))
            gdal_env["AWS_ACCESS_KEY_ID"] = credentials.access_key
            gdal_env["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
            gdal_env["AWS_SESSION_TOKEN"] = credentials.token
            input_file = get_vfs_path(input_file)
        command.append(input_file)

    if output_file:
        command.append(output_file)

    start_time = time_in_ms()
    try:
        get_log().debug(
            "GDAL execution started", action="run_gdal", reason="start", gdal={"command": command_to_string(command)}
        )
        proc = subprocess.run(command, env=gdal_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as cpe:
        get_log().error(
            "GDAL execution has failed",
            action="run_gdal",
            reason="fail",
            stderr=str(cpe.stderr, "utf-8"),
            command=command_to_string(command),
            duration=time_in_ms() - start_time,
        )
        raise GDALExecutionException(f"GDAL {str(cpe.stderr, 'utf-8')}") from cpe

    if proc.stderr:
        get_log().error(
            "GDAL execution has not been successful",
            action="run_gdal",
            reason="fail",
            gdal={"command": command_to_string(command), "stderr": proc.stderr.decode()},
            duration=time_in_ms() - start_time,
        )
        raise GDALExecutionException(proc.stderr.decode())

    stdout = proc.stdout.decode()
    if "-json" in command:
        stdout = json.loads(stdout)
    get_log().debug(
        "GDAL execution ended",
        action="run_gdal",
        reason="success",
        gdal={"command": command_to_string(command), "stdout": stdout},
        duration=time_in_ms() - start_time,
    )

    return proc
