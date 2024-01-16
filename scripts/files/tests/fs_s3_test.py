import json

from boto3 import client, resource
from botocore.exceptions import ClientError
from moto import mock_s3
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest import CaptureFixture, raises

from scripts.files.files_helper import ContentType
from scripts.files.fs_s3 import exists, list_files_in_uri, read, write


@mock_s3  # type: ignore
def test_write() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.file", b"test content")

    resp = boto3_client.get_object(Bucket="testbucket", Key="test.file")
    assert resp["Body"].read() == b"test content"
    assert resp["ContentType"] == "binary/octet-stream"


@mock_s3  # type: ignore
def test_write_content_type() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.tiff", b"test content", ContentType.GEOTIFF.value)
    resp = boto3_client.get_object(Bucket="testbucket", Key="test.tiff")
    assert resp["Body"].read() == b"test content"
    assert resp["ContentType"] == ContentType.GEOTIFF.value


@mock_s3  # type: ignore
def test_read() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    content = read("s3://testbucket/test.file")

    assert content == b"test content"


@mock_s3  # type: ignore
def test_read_bucket_not_found(capsys: CaptureFixture[str]) -> None:
    with raises(ClientError):
        read("s3://testbucket/test.file")

    # python-linz-logger uses structlog which doesn't use stdlib so can't capture the logs with `caplog`
    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_bucket_not_found"


@mock_s3  # type: ignore
def test_read_key_not_found(capsys: CaptureFixture[str]) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    with raises(ClientError):
        read("s3://testbucket/test.file")

    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_key_not_found"


@mock_s3  # type: ignore
def test_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is True


@mock_s3  # type: ignore
def test_directory_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/test.file", Body=b"test content")

    directory_exists = exists("s3://testbucket/hello/")

    assert directory_exists is True


@mock_s3  # type: ignore
def test_exists_bucket_not_exists(capsys: CaptureFixture[str]) -> None:
    file_exists = exists("s3://testbucket/test.file")

    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_bucket_not_found"
    assert file_exists is False


@mock_s3  # type: ignore
def test_exists_object_not_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is False


@mock_s3  # type: ignore
def test_exists_object_starting_with_not_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/hello/another.fi")

    assert file_exists is False


@mock_s3  # type: ignore
def test_list_files_in_uri() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="data/collection.json", Body=b"test content")
    boto3_client.put_object(Bucket="testbucket", Key="data/image.tiff", Body=b"test content")
    boto3_client.put_object(Bucket="testbucket", Key="data/image_meta.xml", Body=b"test content")

    files = list_files_in_uri("s3://testbucket/data/", [".json", "_meta.xml"], boto3_client)

    assert len(files) == 2
    assert "data/collection.json" in files
    assert "data/image_meta.xml" in files
    assert "data/image.tiff" not in files
