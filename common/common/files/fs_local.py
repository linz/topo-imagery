def write(destination: str, source: bytes) -> None:
    """Write the source to the local destination file.

    Args:
        destination (str): The local path to the file to write.
        source (bytes): The source file in bytes.
    """
    with open(destination, "wb") as file:
        file.write(source)


def read(path: str) -> bytes:
    """Read the local file from its path.

    Args:
        path (str): A local path to a file.

    Returns:
        bytes: The file in bytes.
    """
    with open(path, "rb") as file:
        return file.read()
