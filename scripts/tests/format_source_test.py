import linz_logger
from format_source import format_source


def test_format_source_from_basemaps_cli_file() -> None:
    """Based on output from basemaps cli
    example: --source "[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"
    """
    # fmt: off
    source = ["[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"]
    # fmt: on
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 2
    assert file_list == ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]


def test_format_source_single_input() -> None:
    """example: --source s3://test/image_one.tiff"""
    source = ["s3://test/image_one.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 1
    assert file_list == ["s3://test/image_one.tiff"]


def test_format_source_multiple_inputs() -> None:
    """example: --source s3://test/image_one.tiff s3://test/image_two.tiff"""
    source = ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 2
    assert file_list == ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]

def test_format_source_json_loading_error() -> None:
    """example: --source [s3://test/image_one.tiff"""
    source = ["[s3://test/image_one.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 1
    assert file_list == ["[s3://test/image_one.tiff"]
