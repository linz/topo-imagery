import argparse
import json
from os import environ
from typing import List

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
            get_log().debug("Decoding Json Failed", source=source, msg=e)
            raise e
    return source


def parse_source() -> List[str]:
    """Parse the CLI argument '--source' and format it to a list of paths.

    Returns:
        List[str]: A list of paths.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    arguments = parser.parse_args()

    return format_source(arguments.source)


def is_argo() -> bool:
    return bool(environ.get("ARGO_TEMPLATE"))
