from typing import List


def format_source_from_basemaps_cli(source: str) -> List[str]:
    """
    source needs to be split from str to list
    example: ["[\"s3://test/image_one.tiff, \"s3://test/image_two.tiff\"]"]
    """
    source = source.replace("\"","").replace("[", "").replace("]", "")
    file_list = source.split(", ")
    return file_list
