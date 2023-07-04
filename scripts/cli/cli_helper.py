import argparse
import json
from datetime import datetime
from os import environ
from typing import List, Optional

from dateutil import parser, tz
from linz_logger import get_log


def format_source(source: List[str]) -> List[str]:
    """Due to Argo constraints if using the basemaps cli list command
    the source has a string that contains a list that needs to be split.
    example: ["[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"]
    """
    if len(source) == 1 and source[0].startswith("["):
        try:
            source_json: List[str] = json.loads(source[0])
            return source_json
        except json.JSONDecodeError as e:
            get_log().debug("Decoding Json Failed", msg=e)
    return source


def parse_source() -> List[str]:
    """Parse the CLI argument '--source' and format it to a list of paths.

    Returns:
        List[str]: A list of paths.
    """
    parser_args = argparse.ArgumentParser()
    parser_args.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser_args.parse_args()

    return format_source(arguments.source)


def is_argo() -> bool:
    return bool(environ.get("ARGO_TEMPLATE"))


def format_date(date: datetime) -> str:
    """Parse the CLI argument '--date' and format it to UTC.
    Args:
        date: datetime
    Returns:
        str: date and time in UTC
    """
    date_string_nz = f"{date.strftime('%Y-%m-%d')}T00:00:00.000"
    datetime_utc = nzt_datetime_to_utc_datetime(date_string_nz)
    return datetime_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def nzt_datetime_to_utc_datetime(date: str) -> datetime:
    utc_tz = tz.gettz("UTC")
    nz_tz = tz.gettz("Pacific/Auckland")

    try:
        nz_time = parser.parse(date).replace(tzinfo=nz_tz)
    except parser.ParserError as err:
        raise Exception(f"Not a valid date: {err}") from err

    utc_time: datetime = nz_time.astimezone(utc_tz)
    return utc_time


def valid_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        msg = f"not a valid date: {s}"
        raise argparse.ArgumentTypeError(msg) from e


def parse_list(list_s: str, separator: Optional[str] = ";") -> List[str]:
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


def coalesce_multi_single(multi_items: Optional[str], single_item: Optional[str]) -> List[str]:
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
