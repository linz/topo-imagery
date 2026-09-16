import os
import shutil

from geoprocessor_common.files import checksum


def write(destination: str, source: bytes) -> None:
    """Write the source to the local destination file.

    Args:
        destination: The local path to the file to write.
        source: The source file in bytes.
    """
    os.makedirs(os.path.dirname(destination), mode=0o777, exist_ok=True)
    with open(destination, "wb") as file:
        file.write(source)


def copy_file(source_path: str, destination: str) -> None:
    """Copy a local file to another local destination without loading it into memory.

    Args:
        source_path: The local path to the file to copy.
        destination: The local path to the file to write.

    Raises:
        SameFileError: if `source_path` and `destination` are the same file
    """
    os.makedirs(os.path.dirname(destination), mode=0o777, exist_ok=True)
    shutil.copyfile(source_path, destination)


def multihash(path: str) -> str:
    """Get the multihash of a local file without loading it into memory.

    Args:
        path: A local path to a file.

    Returns:
        the multihash of the file content
    """
    return checksum.multihash_from_path(path)


def read(path: str) -> bytes:
    """Read the local file from its path.

    Args:
        path: A local path to a file.

    Returns:
        The file in bytes.
    """
    with open(path, "rb") as file:
        return file.read()


def exists(path: str) -> bool:
    """Check if path (file or directory) exists

    Args:
        path: A local path to a directory or file

    Returns:
        True if the path exists
    """
    return os.path.exists(path)
