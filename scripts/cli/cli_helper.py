import argparse
import json
import warnings
from datetime import datetime
from decimal import Decimal
from typing import Any, NamedTuple

import shapely.geometry
from linz_logger import get_log

from scripts.datetimes import parse_rfc_3339_date
from scripts.files.fs import read


class InputParameterError(Exception):
    pass


class TileFiles(NamedTuple):
    output: str
    """ The tile name of the output file that will be created """

    inputs: list[str]
    """ The list of input files to be used to create the output file """

    includeDerived: bool = False
    """ Whether the STAC Item should include the derived_from links """


def get_tile_files(source: str) -> list[TileFiles]:
    """Transform a JSON string representing a list of input file paths and output tile name created
    by `argo-tasks` (see examples) to a list of `TileFiles`

    Args:
        source: JSON string containing representing a list of input file paths and output tile name

    Raises:
        InputParameterError: for any parsing error

    Returns:
        a list of `TileFiles` namedtuple

    Example:
        >>> get_tile_files('[{"output": "CE16_5000_1001", "input": ["s3://bucket/SN9457_CE16_10k_0501.tif"]}]')
        [TileFiles(output='CE16_5000_1001', inputs=['s3://bucket/SN9457_CE16_10k_0501.tif'], includeDerived=False)]
    """
    try:
        source_json: list[TileFiles] = json.loads(
            source,
            object_hook=lambda d: TileFiles(
                inputs=d["input"], output=d["output"], includeDerived=d.get("includeDerived", False)
            ),
        )
    except (json.decoder.JSONDecodeError, KeyError) as e:
        get_log().error(type(e).__name__, error=str(e))
        raise InputParameterError("An error occurred while parsing the input file") from e

    return source_json


def load_input_files(path: str) -> list[TileFiles]:
    """Load the TileFiles from a JSON input file containing a list of output and input files.
    Args:
        path: path to a JSON file listing output name and input files

    Returns:
        a list of `TileFiles` namedtuple
    """
    source = json.dumps(json.loads(read(path)))

    try:
        tile_files: list[TileFiles] = get_tile_files(source)
        return tile_files
    except InputParameterError as e:
        get_log().error("An error occurred while getting tile_files", error=str(e))
        raise e


def valid_date(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return parse_rfc_3339_date(s)
    except ValueError as e:
        msg = f"not a valid date: {s}"
        raise argparse.ArgumentTypeError(msg) from e


def parse_list(list_s: str, separator: str | None = ";") -> list[str]:
    """Transform a string representing a list to a list of strings
    example: "foo; bar; foo bar" -> ["foo", "bar", "foo bar"]

    Args:
        list_s: string representing a list to transform
        separator: separator of the list

    Returns:
        a list of strings
    """
    if list_s:
        return [s.strip() for s in list_s.split(separator) if s != ""]
    return []


def coalesce_multi_single(multi_items: str | None, single_item: str | None) -> list[str]:
    """Coalesce strings containing either semicolon delimited values or a single
    value into a list. `single_item` is used only if `multi_items` is falsy.
    If both are falsy, an empty list is returned.

    Args:
        multi_items: string with semicolon delimited values
        single_item: string with a single value

    Returns:
        a list of values
    """
    output = []
    if multi_items:
        output.extend(parse_list(multi_items))
    elif single_item:
        output.append(single_item)
    return output


def str_to_gsd(value: str) -> Decimal:
    number_value = value.removesuffix("m")
    if number_value != value:
        warnings.warn(
            "Specifying GSD with a trailing 'm' character will not be supported in future versions. "
            "Please use a plain decimal number like '0.3' instead.",
            DeprecationWarning,
        )

    return Decimal(number_value)


def str_to_bool(value: str) -> bool:
    """Transform a string to a boolean value

    Example:
        >>> str_to_bool("true")
        True

    Args:
        str: string representing a boolean value

    Raises:
        ArgumentTypeError: if the string is not "true" or "false"

    Returns:
        bool: True if "true", False if "false"
    """
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean (must be exactly 'true' or 'false'): {value}")


def str_to_list_or_none(values: str) -> list[Decimal] | None:
    """Transform a string to an empty list of list with 2 values. Return None if the string is empty.

    Example:
        >>> str_to_list_or_none('2,4')
        [Decimal('2'), Decimal('4')]
        >>> str_to_list_or_none('') is None
        True

    Args:
        str: string representing a list or an empty string

    Raises:
        ArgumentTypeError: if the string is not empty and does not contain exactly 2 values

    Returns:
        None or a list of 2 values
    """
    if not values:
        return None
    result = [Decimal(value) for value in values.split(",")]
    if len(result) != 2:
        raise argparse.ArgumentTypeError(f"Invalid list - must be blank or exactly 2 values x,y. Received: {values}")
    return result


def get_geometry_from_geojson(geojson: dict[str, Any], file_path: str) -> shapely.geometry.base.BaseGeometry:
    """Extracts a geometry from a GeoJSON file and logs errors if the geometry is invalid.

    :param geojson: The contents of the GeoJSON file.
    :param file_path: Path to the GeoJSON file.
    :return: A Shapely BaseGeometry object if successful, otherwise raises an exception.
    """
    get_log().debug(f"importing geometry from {file_path}")
    try:
        return shapely.geometry.shape(geojson["features"][0]["geometry"])
    except (IndexError, KeyError) as e:
        error_message = "The supplied GeoJSON does not contain a valid geometry:"
        get_log().error(
            error_message,
            file=file_path,
            error=str(e),
        )
        e.add_note(f"{error_message} {file_path}")
        raise
