import os
from enum import Enum
from typing import Optional

from scripts.gdal.gdalinfo import GdalInfo, gdal_info


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


def is_GTiff(path: str, gdalinfo_data: Optional[GdalInfo] = None) -> bool:
    """Verifies if a file is a GTiff based on the presence of the
    `coordinateSystem`.

    Args:
        path: a path to a file
        gdalinfo_data: gdalinfo of the file. Defaults to None.

    Returns:
        True if the file is a GTiff
    """
    if not gdalinfo_data:
        gdalinfo_data = gdal_info(path)
    if not "coordinateSystem" in gdalinfo_data:
        return False
    if gdalinfo_data["driverShortName"] == "GTiff":
        return True
    return False
