import os
from concurrent.futures import Future, ThreadPoolExecutor
from tempfile import TemporaryDirectory

from boto3 import client
from geoprocessor_common.aws.aws_helper import is_s3
from geoprocessor_common.files import fs_local, fs_s3
from geoprocessor_common.files.checksum import multihash_as_hex
from linz_logger import get_log


def write(destination: str, source: bytes, content_type: str | None = None) -> str:
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


def multihash(path: str) -> str:
    """Get the multihash of a file without loading it into memory.

    Args:
        path: A path to a file.

    Returns:
        the multihash of the file content
    """
    if is_s3(path):
        return fs_s3.multihash(path)

    try:
        return fs_local.multihash(path)
    except FileNotFoundError as error:
        raise NoSuchFileError(path) from error


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
        except client("s3").exceptions.ClientError as ce:
            # Error Code can be found here:
            # https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList
            if ce.response["Error"]["Code"] == "NoSuchKey":
                raise NoSuchFileError(path) from ce

    try:
        return fs_local.read(path)
    except FileNotFoundError as error:
        raise NoSuchFileError(path) from error


def copy(source: str, target: str, content_type: str | None = None) -> str:
    """Copy a `source` file to a `target`, streaming it rather than holding it in memory.

    Unlike `write()` this is not limited to 5GB when the target is on `s3`.

    Args:
        source: A path to a file to copy
        target: A path of the copy to create
        content_type: A standard Media Type describing the format of the contents.

    Raises:
        NoSuchFileError: if the source does not exist

    Returns:
        the multihash of the file content
    """
    get_log().debug("copy", source=source, target=target)

    try:
        if is_s3(source) and is_s3(target):
            with TemporaryDirectory() as tmp_path:
                local_copy = os.path.join(tmp_path, os.path.basename(target))
                fs_s3.download(source, local_copy)
                return fs_s3.upload(local_copy, target, content_type)

        if is_s3(source):
            fs_s3.download(source, target)
            return fs_local.multihash(target)

        if is_s3(target):
            return fs_s3.upload(source, target, content_type)

        fs_local.copy_file(source, target)
        return fs_local.multihash(target)
    except FileNotFoundError as error:
        raise NoSuchFileError(source) from error
    except client("s3").exceptions.ClientError as ce:
        # https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList
        if ce.response["Error"]["Code"] == "NoSuchKey":
            raise NoSuchFileError(source) from ce
        raise


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


def write_all(inputs: list[str], target: str, concurrency: int | None = 4, generate_name: bool | None = True) -> list[str]:
    """Writes list of files to target destination using multithreading.
    Args:
        inputs: list of files to read
        target: target folder to write to
        concurrency: max thread pool workers
        generated_name: create a target file name based on multihash the source filename

    Returns:
        list of written file paths
    """
    results: list[Future] = []  # type: ignore
    written_tiffs: list[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for input_ in inputs:
            results.append(executor.submit(write_file, input_, target, generate_name))

    for future in results:
        if future.exception():
            get_log().warn("Failed Read-Write", error=future.exception())
        else:
            written_tiffs.append(future.result())

    if len(inputs) != len(written_tiffs):
        get_log().error("Missing Files", count=len(inputs) - len(written_tiffs))
        raise Exception("Not all mandatory source files were written")

    return written_tiffs


def write_sidecars(inputs: list[str], target: str, concurrency: int | None = 4) -> None:
    """Writes list of files (if found) to target destination using multithreading.
    The copy of the files have a generated file name (@see `write_file`)

    Args:
        inputs: list of files to read
        target: target folder to write to
        concurrency: max thread pool workers
    """
    results: list[Future] = []  # type: ignore
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for input_ in inputs:
            results.append(executor.submit(write_file, input_, target))

    for future in results:
        future_ex = future.exception()
        if isinstance(future_ex, NoSuchFileError):
            get_log().info("No sidecar file found; skipping", error=future.exception())
        else:
            get_log().info("wrote_sidecar_file", path=future.result())


def write_file(input_: str, target: str, generate_name: bool | None = True) -> str:
    """Read a file from a path and write it to a target path.
    Args:
        input: A path to a file to read.
        target: A path to write the file to.
        generate_name: create a target file name based on multihash the source filename

    Returns:
        str: Target file name.
    """
    get_log().info(f"Trying write from file: {input_}")

    if generate_name:
        file_name, file_extension = os.path.splitext(input_)
        target_file_name = f"{multihash_as_hex(str.encode(file_name))}{file_extension}"
    else:
        target_file_name = os.path.basename(input_)

    target_path = os.path.join(target, target_file_name)
    copy(input_, target_path)
    return target_path


class NoSuchFileError(Exception):
    def __init__(self, path: str) -> None:
        self.message = f"File not found: {path}"
        self.path = path
