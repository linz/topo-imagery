from scripts.aws.aws_helper import is_s3
from scripts.files import fs_local, fs_s3


def write(destination: str, source: bytes) -> None:
    """Write a file from its source to a destination path.

    Args:
        destination (str): A path to where the file will be written.
        source (bytes): The source file in bytes.
    """
    if is_s3(destination):
        fs_s3.write(destination, source)
    else:
        fs_local.write(destination, source)


def read(path: str) -> bytes:
    """Read a file from its path.

    Args:
        path (str): A path to a file to read.

    Returns:
        bytes: The bytes content of the file.
    """
    if is_s3(path):
        return fs_s3.read(path)

    return fs_local.read(path)


def exists(path: str) -> bool:
    """Check if path (file or directory) exists

    Args:
        path: A path to a directory or file

    Returns:
        True if the path exists
    """
    if is_s3(path):
        return fs_s3.exists(path)
    return fs_local.exists(path)
