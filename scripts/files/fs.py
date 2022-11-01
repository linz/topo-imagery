from linz_logger import get_log

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


def rename(path: str, new_path: str) -> None:
    """Rename a file (path to new_path).

    Args:
        path (str): the path of the original file.
        new_path (str): the path of which the file should be renamed to.

    Raises:
        Exception: an exception if the path are not on the same file system.
    """
    if path == new_path:
        get_log().info("rename_skipped_same_name", path=path, destination=new_path)
    else:
        if is_s3(path) and is_s3(new_path):
            fs_s3.rename(path, new_path)
        elif not is_s3(path) and not is_s3(new_path):
            fs_local.rename(path, new_path)
        else:
            raise Exception("The files to rename have to be on the same file system.")
