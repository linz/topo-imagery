import os
import subprocess
from shutil import rmtree
from tempfile import mkdtemp

from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.files.fs import copy
from scripts.logging.time_helper import time_in_ms


class PDALExecutionException(Exception):
    pass


def get_pdal_command(command: str, options: list[str]) -> list[str]:
    """Build a `pdal` command.

    Args:
        command: pdal command to run (e.g. 'translate', 'info', etc.)
        options: options to pass to the pdal command

    Returns:
        a list of arguments for `pdal`
    """
    get_log().info("pdal command", command=command, options=options)

    pdal_command: list[str] = [command]
    pdal_command.extend(options)

    return pdal_command


pdal_translate_add_proj_command = get_pdal_command(
    "translate",
    [
        "--readers.las.spatialreference=EPSG:2193+7839",
        "--writers.las.filesource_id=0",
        "--writers.las.forward=all",
    ],
)

pdal_info_command = get_pdal_command(
    "info",
    ["--metadata", "--summary", "--json"],
)


def run_pdal(
    command_options_args: list[str],
    input_file: str | None = None,
    output_file: str | None = None,
) -> "subprocess.CompletedProcess[bytes]":
    """Run the PDAL command. The permissions to access to the input file are applied to the pdal environment.

        Args:
            command_options_args: list of command, options and arguments to be passed to the PDAL command
            input_file: /path/to/the/input_file
            output_file: /path/to/the/output_file

    Raises:
            PDALExecutionException: If no input file is provided or if something goes wrong during the execution of the command

        Returns:
            subprocess.CompletedProcess: the output process.
    """
    start_time = time_in_ms()
    pdal_env = os.environ.copy()
    pdal_exec = os.environ.get("PDAL_EXECUTABLE", "pdal")
    pdal_command = [pdal_exec, *command_options_args]

    if not input_file:
        raise PDALExecutionException("An input file must be provided")

    temp_dir = mkdtemp()
    if is_s3(input_file):  # Download the file from S3
        input_file = copy(source=input_file, target=os.path.join(temp_dir, input_file.split("/")[-1]))

    pdal_command.append(input_file)

    temp_output_file = None
    if output_file:
        if is_s3(output_file):
            temp_output_file = os.path.join(temp_dir, output_file.split("/")[-1])
            pdal_command.append(temp_output_file)
        else:
            pdal_command.append(output_file)

    try:
        get_log().debug("run_pdal_start", command=" ".join(pdal_command))
        proc = subprocess.run(pdal_command, env=pdal_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as cpe:
        get_log().error("run_pdal_failed", command=" ".join(pdal_command), error=str(cpe.stderr, "utf-8"))
        raise PDALExecutionException(f"PDAL {str(cpe.stderr, 'utf-8')}") from cpe
    finally:
        get_log().info("run_pdal_end", command=" ".join(pdal_command), duration=time_in_ms() - start_time)

    if proc.stderr:
        get_log().warning("run_pdal_stderr", command=" ".join(pdal_command), stderr=proc.stderr.decode())

    rmtree(temp_dir)
    if temp_output_file and output_file:  # Upload the file to S3
        copy(source=temp_output_file, target=output_file)

    get_log().trace("run_pdal_succeeded", command=" ".join(pdal_command), stdout=proc.stdout.decode())

    return proc
