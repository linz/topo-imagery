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
    get_log().debug("write", path=destination)
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
    get_log().debug("read", path=path)
    if is_s3(path):
        try:
            return fs_s3.read(path)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html#parsing-error-responses-and-catching-exceptions-from-aws-services
        except resource("s3").meta.client.exceptions.ClientError as ce:
            # Error Code can be found here:
            # https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList
            if ce.response["Error"]["Code"] == "NoSuchKey":
                raise NoSuchFileError(path) from ce

    try:
        return fs_local.read(path)
    except FileNotFoundError as error:
        raise NoSuchFileError(path) from error


def copy(source: str, target: str) -> str:
    """Copy a `source` file to a `target`.

    Args:
        source: A path to a file to copy
        target: A path of the copy to create

    Returns:
        The path of the file created
    """
    source_content = read(source)
    return write(target, source_content)


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
        results = {write_file(executor, input_, target): input_ for input_ in inputs}
        for future in as_completed(results):
            future_ex = future.exception()
            if isinstance(future_ex, NoSuchFileError):
                get_log().info("No sidecar file found; skipping", path=future_ex.path)
            else:
                get_log().info("wrote_sidecar_file", path=future.result())


def write_file(executor: ThreadPoolExecutor, input_: str, target: str) -> Future[str]:
    """Read a file from a path and write it to a target path.

    Args:
        executor: A ThreadPoolExecutor instance.
        input_: A path to a file to read.
        target: A path to write the file to.

    Returns:
        Future[str]: The result of the execution.
    """
    get_log().info(f"Trying write from file: {input_}")
    try:
        return executor.submit(copy, input_, os.path.join(target, f"{os.path.basename(input_)}"))
    except NoSuchFileError as nsfe:
        future: Future[str] = Future()
        future.set_exception(nsfe)
        return future


class NoSuchFileError(Exception):
    def __init__(self, path: str) -> None:
        self.message = f"File not found: {path}"
        self.path = path
