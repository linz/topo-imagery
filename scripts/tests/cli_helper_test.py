import argparse
from datetime import datetime

import pytest

from scripts.cli.cli_helper import format_date, format_source, valid_date


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


def test_format_date() -> None:
    """example: --start_datetime 2022-01-22"""
    s = "2022-01-22"
    assert format_date(datetime.strptime(s, "%Y-%m-%d")) == "2022-01-21T11:00:1642719600Z"


def test_valid_date() -> None:
    """example:  --start_datetime 2022-01-22"""
    assert valid_date("2022-01-22") == datetime.strptime("2022-01-22", "%Y-%m-%d")


def test_invalid_date() -> None:
    """example:  --start_datetime 22-01-22"""
    with pytest.raises(argparse.ArgumentTypeError) as e:
        valid_date("22-01-22")
        assert "not a valid date" in str(e.value).lower()
    with pytest.raises(argparse.ArgumentTypeError) as e:
        valid_date("2022-22-01")
        assert "not a valid date" in str(e.value).lower()
    with pytest.raises(argparse.ArgumentTypeError) as e:
        valid_date("22-01-2022")
        assert "not a valid date" in str(e.value).lower()
    with pytest.raises(argparse.ArgumentTypeError) as e:
        valid_date("2022/01/22")
        assert "not a valid date" in str(e.value).lower()
