import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.files import fs_local, fs_s3


def write(destination: str, source: bytes) -> str:
    """Write a file from its source to a destination path.

    Args:
        destination: A path to where the file will be written.
        source: The source file in bytes.
    """
    if is_s3(destination):
        fs_s3.write(destination, source)
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
        return fs_s3.read(path)

    return fs_local.read(path)


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


def write_all(inputs: List[str], target: str, concurrency: Optional[int] = 10) -> List[str]:
    """Writes list of files to target destination using multithreading.

    Args:
        inputs: list of files to read
        target: target folder to write to

    Returns:
        list of written file paths
    """
    written_tiffs: List[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futuress = {
            executor.submit(write, os.path.join(target, f"{input.split('/')[-1]}"), read(input)): input for input in inputs
        }
        for future in as_completed(futuress):
            if future.exception():
                get_log().warn("Failed Read-Write", error=future.exception())
            else:
                written_tiffs.append(future.result())

    if len(inputs) != len(written_tiffs):
        get_log().error("Missing Files", count=len(inputs) - len(written_tiffs))
        raise Exception("Not all source files were written")
    return written_tiffs


def find_sidecars(inputs: List[str], extensions: List[str]) -> List[str]:
    """Searches for sidecar files.
     A sidecar files is a file with the same name as the input file but with a different extension.

    Args:
        inputs: list of input files to search for extensions
        extensions: the sidecar file extensions

    Returns:
        list of existing sidecar files
    """
    sidecars = []
    for file in inputs:
        for extension in extensions:
            sidecar = f"{file.split('.')[0]}{extension}"
            if exists(sidecar):
                sidecars.append(sidecar)
    return sidecars
