import os
from enum import Enum

SUFFIX_JSON = ".json"
SUFFIX_FOOTPRINT = "_footprint.geojson"


class ContentType(str, Enum):
    GEOTIFF = "image/tiff; application=geotiff; profile=cloud-optimized"
    JSON = "application/json"
    GEOJSON = "application/geo+json"
    """ https://www.iana.org/assignments/media-types/application/geo+json"""
    JPEG = "image/jpeg"


def get_file_name_from_path(path: str) -> str:
    """Get the file name from a path.

    Args:
        path: a path to a file

    Returns:
        the name of the file

    Example:
        >>> get_file_name_from_path("/a/path/to/file.ext")
        'file'
    """
    return os.path.splitext(os.path.basename(path))[0]


def is_tiff(path: str) -> bool:
    """Verify if file is a TIFF.

    Args:
        path: a path to a file

    Returns:
        True if the file has a `.tiff` or `.tif` extension

    Examples:
        >>> is_tiff("/a/path/to/file.tif")
        True
        >>> is_tiff("/a/path/to/file.jpg")
        False
    """
    return path.lower().endswith((".tiff", ".tif"))


def is_json(path: str) -> bool:
    """Verify if file is a JSON.

    Args:
        path: a path to a file

    Returns:
        True if the file has a `.json` extension

    Examples:
        >>> is_json("/a/path/to/file.json")
        True
        >>> is_json("/a/path/to/file.csv")
        False
    """
    return path.lower().endswith(".json")


def convert_s3_paths(files_flat: list[str]) -> list[str]:
    """
    Convert a flat list of S3 paths into a flat list with appropriate /vsis3/ prefixes.

    Parameters:
    files_flat (list of str): Flat list containing S3 file paths.

    Returns:
    list of str: Flat list with converted /vsis3/ paths.
    """

    return [path.replace("s3://", "/vsis3/") for path in files_flat]


def flatten_file_list(files_nested: list[list[str]]) -> list[str]:
    """
    Convert a nested list of paths into a flat list.

    Parameters:
    files_nested (list of list of str): Nested list containing file paths.

    Returns:
    list of str: Flattened list.
    """
    return [path for sublist in files_nested for path in sublist]
