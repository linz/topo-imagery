import os
from enum import Enum


class ContentType(str, Enum):
    GEOTIFF = "image/tiff; application=geotiff; profile=cloud-optimized"
    JSON = "application/json"
    # https://www.iana.org/assignments/media-types/application/geo+json
    GEOJSON = "application/geo+json"
    JPEG = "image/jpeg"


def get_file_name_from_path(path: str) -> str:
    """Get the file name from a path.

    Args:
        path: a path to a file

    Returns:
        the name of the file

    Example:
        ```
        >>> get_file_name_from_path("/a/path/to/file.ext")
        "file.ext"
        ```
    """
    return os.path.splitext(os.path.basename(path))[0]


def is_tiff(path: str) -> bool:
    """Verify if file is a TIFF.

    Args:
        path: a path to a file

    Returns:
        True if the file is a TIFF

    Examples:
        ```
        >>> is_tiff("/a/path/to/file.tif")
        True
        >>> is_tiff("/a/path/to/file.jpg")
        False
        ```
    """
    return path.lower().endswith((".tiff", ".tif"))


def is_json(path: str) -> bool:
    """Verify if file is a JSON.

    Args:
        path: a path to a file

    Returns:
        True if the file is a JSON

    Examples:
        ```
        >>> is_tiff("/a/path/to/file.json")
        True
        >>> is_tiff("/a/path/to/file.csv")
        False
        ```
    """
    return path.lower().endswith(".json")
