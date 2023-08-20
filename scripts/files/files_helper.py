import os

from scripts.gdal.gdalinfo import gdal_info


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


def is_GTiff(path: str) -> bool:
    """Verifies if a file is a GTiff

    Args:
        path: a path to a file

        Returns:
        True if the file is a GTiff
    """
    gdal_data = gdal_info(path)
    if gdal_data["cornerCoordinates"]["upperLeft"] == [0, 0]:
        return False
    if gdal_data["driverShortName"] == "GTiff":
        return True
    return False


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
