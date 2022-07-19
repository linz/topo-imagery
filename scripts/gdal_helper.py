import os
import subprocess
from typing import List, Optional

from aws_helper import get_bucket_name_from_path, get_credentials, is_s3
from linz_logger import get_log


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
    command: List[str], input_file: str = "", output_file: str = "", input_file_index: Optional[int] = None
) -> "subprocess.CompletedProcess[bytes]":
    """Run the GDAL command. The permissions to access to the input file are applied to the gdal environment.

    Args:
        command (List[str]): each arguments of the GDAL command.
        input_file (str, optional): the input file path. Defaults to "".
        output_file (str, optional): the output file path. Defaults to "".

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
    if input_file_index:
        command.insert(input_file_index, input_file)
    else:
        command.append(input_file)

    if output_file:
        command.append(output_file)
    try:
        get_log().debug("run_gdal", command=command_to_string(command))
        proc = subprocess.run(command, env=gdal_env, check=True, capture_output=True)
    except subprocess.CalledProcessError as cpe:
        get_log().error("run_gdal_failed", command=command_to_string(command), error=str(cpe.stderr, "utf-8"))
        raise cpe
    get_log().debug("run_gdal_translate_succeded", command=command_to_string(command))

    return proc
