import os
from typing import List, Optional, Tuple


def write(destination: str, source: bytes) -> None:
    """Write the source to the local destination file.

    Args:
        destination (str): The local path to the file to write.
        source (bytes): The source file in bytes.
    """
    with open(destination, "wb") as buffer:
        buffer.write(source)


def read(path: str) -> bytes:
    """Read the local file from its path.

    Args:
        path (str): A local path to a file.

    Returns:
        bytes: The file in bytes.
    """
    with open(path, "rb") as buffer:
        return buffer.read()


def scandir(directory: str, extensions: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """Scan folders (recursively) and files in local directory. The files can be filter on extensions.

    Args:
        directory (str): A path to a local directory.
        extensions (Optional[List[str]], optional): A list of extensions to filter on. Defaults to None (no filter).

    Returns:
        Tuple[List[str], List[str]]: The folders and files lists.
    """
    folders, files = [], []

    for element in os.scandir(directory):
        if element.is_dir():
            folders.append(element.path)
        if element.is_file():
            if os.path.splitext(element.name)[1].lower() in extensions:
                files.append(element.path)

    for f in folders:
        f_folders, f_files = scandir(f, extensions)
        folders.extend(f_folders)
        files.extend(f_files)

    return folders, files
