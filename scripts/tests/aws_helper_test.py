import pytest

from scripts.aws_helper import parse_path


def test_parse_path() -> None:
    s3_path = "s3://bucket-name/path/to/the/file.test"
    bucket_name, file_path = parse_path(s3_path)

    assert bucket_name == "bucket-name"
    assert file_path == "/path/to/the/file.test"
