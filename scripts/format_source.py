import json
from typing import List, cast


def format_source(source: List[str]) -> List[str]:
    """If source from basemaps cli it has a string which contains a list that needs to be split
    example: ["[\"s3://test/image_one.tiff, \"s3://test/image_two.tiff\"]"]
    """
    if len(source) == 1 and source[0].startswith("["):
        return cast(List[str], json.loads(source[0]))
    return source
