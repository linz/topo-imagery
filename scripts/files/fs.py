import os
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import List, Optional

from boto3 import resource
from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.files import fs_local, fs_s3


def write(destination: str, source: bytes, content_type: Optional[str] = None) -> str:
    """Write a file from its source to a destination path.

    Args:
        destination: A path to where the file will be written.
        source: The source file in bytes.
        content_type: A standard Media Type describing the format of the contents.
    """
    if is_s3(destination):
        fs_s3.write(destination, source, content_type)
    else:
        fs_local.write(destination, source)
    return destination


def read(path: str) -> bytes:
    """Read a file from its path.

    Args:
        path: A path to a file to read.

    Returns:
        bytes: The bytes content of the file.
    """
    if is_s3(path):
        try:
            return fs_s3.read(path)
        except resource("s3").meta.client.exceptions.NoSuchKey as error:
            raise NoSuchFileError from error

    try:
        return fs_local.read(path)
    except FileNotFoundError as error:
        raise NoSuchFileError from error


def exists(path: str) -> bool:
    """Check if path (file or directory) exists.

    Args:
        path: A path to a directory or file

    Returns:
        bool: True if the path exists
    """
    if is_s3(path):
        return fs_s3.exists(path)
    return fs_local.exists(path)


def write_all(inputs: List[str], target: str, concurrency: Optional[int] = 4) -> List[str]:
    """Writes list of files to target destination using multithreading.

    Args:
        inputs: list of files to read
        target: target folder to write to
        concurrency: max thread pool workers

    Returns:
        list of written file paths
    """
    written_tiffs: List[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futuress = {write_file(executor, input_, target): input_ for input_ in inputs}
        for future in as_completed(futuress):
            if future.exception():
                get_log().warn("Failed Read-Write", error=future.exception())
            else:
                written_tiffs.append(future.result())

    if len(inputs) != len(written_tiffs):
        get_log().error("Missing Files", count=len(inputs) - len(written_tiffs))
        raise Exception("Not all mandatory source files were written")

    return written_tiffs


def write_sidecars(inputs: List[str], target: str, concurrency: Optional[int] = 4) -> None:
    """Writes list of files to target destination using multithreading.

    Args:
        inputs: list of files to read
        target: target folder to write to
        concurrency: max thread pool workers

    Returns:

    """
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        try:
            results = {write_file(executor, input_, target): input_ for input_ in inputs}
            for future in as_completed(results):
                get_log().info("wrote_sidecar_file", path=future.result())
        except NoSuchFileError:
            get_log().info("No sidecar file found; skipping")


def write_file(executor: ThreadPoolExecutor, input_: str, target: str) -> Future[str]:
    """Read a file from a path and write it to a target path.

    Args:
        executor: A ThreadPoolExecutor instance.
        input_: A path to a file to read.
        target: A path to write the file to.

    Returns:
        Future[str]: The result of the execution.
    """
    return executor.submit(write, os.path.join(target, f"{os.path.basename(input_)}"), read(input_))


class NoSuchFileError(Exception):
    pass
