import argparse
import json
import sys
from datetime import datetime
from os import environ
from typing import List, NamedTuple, Optional

from dateutil import parser, tz
from linz_logger import get_log


class TileFiles(NamedTuple):
    output: str
    input: List[str]


def format_source(source: str) -> List[TileFiles]:
    """Transform a list of dictionaries (Argo Workflows) to a list of `TileFiles`

    Args:
        input: file contents string

    Returns:
        a list of `TileFiles` namedtuple

    Example:
    ```
    >>> format_input([{'output': 'CE16_5000_1001', 'input': ['s3://bucket/SN9457_CE16_10k_0501.tif']}])
    [TileFiles(output='CE16_5000_1001', input=['s3://bucket/SN9457_CE16_10k_0501.tif'])])]
    ```
    """
    try:
        source_json: List[TileFiles] = json.loads(
            source, object_hook=lambda d: TileFiles(input=d["input"], output=d["output"])
        )
    except json.JSONDecodeError as e:
        get_log().error("Decoding Json Failed", msg=e)
        sys.exit(1)
    return source_json


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
