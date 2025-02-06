import argparse
import json
import warnings
from datetime import datetime
from decimal import Decimal
from os import environ
from typing import NamedTuple

from linz_logger import get_log

from scripts.datetimes import format_rfc_3339_nz_midnight_datetime_string, parse_rfc_3339_date
from scripts.files.files_helper import ContentType, get_derived_from_paths, get_stac_item_path, get_standardised_file_path
from scripts.files.fs import exists, read, write
from scripts.gdal.gdal_helper import gdal_info
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.create_stac import create_item


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


def is_argo() -> bool:
    return bool(environ.get("ARGO_TEMPLATE"))


def valid_date(s: str) -> datetime:
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


def item_stac_wrapper(tile_files: list[TileFiles], arguments: argparse.Namespace) -> None:
    """Reusable wrapper around create_items that can be used to create STAC Items
    Args:
        tile_files: List of `TileFiles` to create STAC Item objects for
        arguments: argparse Namespace of CLI input arguments
    """
    # When tile_files has includeDerived field, start_datetime and end_datetime are optional
    if arguments.start_datetime is None or arguments.end_datetime is None:
        for tile in tile_files:
            if not tile.includeDerived:
                raise Exception("--start_datetime and --end_datetime are required if standardising non-derived files.")
        start_datetime = ""
        end_datetime = ""
    else:
        start_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.start_datetime)
        end_datetime = format_rfc_3339_nz_midnight_datetime_string(arguments.end_datetime)

    for tile in tile_files:
        derived_from_paths = []
        stac_item_path = get_stac_item_path(tile.output, arguments.target)
        standardized_file_path = get_standardised_file_path(tile.output, arguments.target)
        if not exists(standardized_file_path):
            get_log().info("Skipping STAC creation for empty output image", path=standardized_file_path)
            continue

        if tile.includeDerived:
            # Transform the TIFF paths to JSON path to point to STAC Items,
            # assuming the STAC Items are in the same directory as the TIFF files
            derived_from_paths = get_derived_from_paths(tile.inputs)

        if not exists(stac_item_path):
            # Create STAC and save in target
            item = create_item(
                standardized_file_path,
                start_datetime,
                end_datetime,
                arguments.collection_id,
                environ["GDAL_VERSION"],
                arguments.current_datetime,
                gdal_info(standardized_file_path),
                derived_from_paths,
                arguments.odr_url,
            )
            write(stac_item_path, dict_to_json_bytes(item.stac), content_type=ContentType.GEOJSON.value)
            get_log().info("stac_saved", path=stac_item_path)
