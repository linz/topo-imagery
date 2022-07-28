import boto3
from moto import mock_s3
from moto.s3.responses import DEFAULT_REGION_NAME

from scripts.files.fs_s3 import read, write


@mock_s3
def test_write() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.file", b"test content")

    resp = client.get_object(Bucket="testbucket", Key="test.file")
    assert resp["Body"].read() == b"test content"


@mock_s3
def test_read() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    content = read("s3://testbucket/test.file")

    assert content == b"test content"


@mock_s3
def test_read_bucket_not_found(capsys) -> None:
    content = read("s3://testbucket/test.file")
    sysout = capsys.readouterr()

    assert "read_s3_bucket_not_found" in sysout.out
    assert content is None


@mock_s3
def test_read_file_not_found(capsys) -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    content = read("s3://testbucket/test.file")
    sysout = capsys.readouterr()

    assert "read_s3_file_not_found" in sysout.out
    assert content is None
