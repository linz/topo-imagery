import os
from enum import Enum


# TODO: make a suffix class?
SUFFIX_JSON = ".json"
SUFFIX_FOOTPRINT = "_footprint.geojson"
SUFFIX_STANDARDISED_TIFF = ".tiff"


class ContentType(str, Enum):
    GEOTIFF = "image/tiff; application=geotiff; profile=cloud-optimized"
    JSON = "application/json"
    GEOJSON = "application/geo+json"
    """ https://www.iana.org/assignments/media-types/application/geo+json"""
    JPEG = "image/jpeg"

# TODO: refactor to make one multi-purpose function
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


def get_footprint_file_path(tile_output: str, target: str) -> str:
    """Get the path of the footprint file.

    Returns:
        a file path
    """
    footprint_file_name = tile_output + SUFFIX_FOOTPRINT
    footprint_file_path = os.path.join(target, footprint_file_name)

    return footprint_file_path


def get_stac_item_path(tile_output: str, target: str) -> str:
    """Get the path of the stac item file.

    Returns:
        a file path
    """
    stac_item_name = tile_output + SUFFIX_JSON
    stac_item_path = os.path.join(target, stac_item_name)

    return stac_item_path


def get_standardised_file_path(tile_output: str, target: str) -> str:
    """Get the path of the standardised file.

    Returns:
        a file path
    """
    standardised_file_name = tile_output + SUFFIX_STANDARDISED_TIFF
    standardised_file_path = os.path.join(target, standardised_file_name)

    return standardised_file_path


def get_derived_from_paths(paths: list[str]) -> list[str]:
    """Get the path(s) of the STAC Items associated to the TIFF files from which the final output is derived.

    Returns:
        a list of STAC Item JSON file paths
    """
    # Transform the TIFF paths to JSON path to point to STAC Items,
    # assuming the STAC Items are in the same directory as the TIFF files

    return [f"{os.path.splitext(path)[0]}.json" for path in paths]


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
