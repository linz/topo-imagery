from scripts.aws.aws_helper import parse_path
from scripts.cli.cli_helper import is_argo


def test_parse_path_s3() -> None:
    s3_path = "s3://bucket-name/path/to/the/file.test"
    path = parse_path(s3_path)

    assert path.bucket == "bucket-name"
    assert path.key == "path/to/the/file.test"


def test_parse_path_local() -> None:
    local_path = "/home/tmp/file.test"
    _, file_path = parse_path(local_path)

    assert file_path == "/home/tmp/file.test"


def test_is_argo() -> None:
    assert not is_argo()
