from scripts.aws.aws_helper import is_argo, parse_path


def test_parse_path() -> None:
    s3_path = "s3://bucket-name/path/to/the/file.test"
    path = parse_path(s3_path)

    assert path.bucket == "bucket-name"
    assert path.key == "path/to/the/file.test"


def test_is_argo() -> None:
    assert not is_argo()
