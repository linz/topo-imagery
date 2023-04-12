import json

import boto3
import botocore
import pytest
from moto import mock_s3
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest import CaptureFixture

from scripts.files.fs_s3 import exists, read, write


@mock_s3  # type: ignore
def test_write() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.file", b"test content")

    resp = client.get_object(Bucket="testbucket", Key="test.file")
    assert resp["Body"].read() == b"test content"


@mock_s3  # type: ignore
def test_read() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    content = read("s3://testbucket/test.file")

    assert content == b"test content"


@mock_s3  # type: ignore
def test_read_bucket_not_found(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(botocore.exceptions.ClientError):
        read("s3://testbucket/test.file")

    # python-linz-logger uses structlog which doesn't use stdlib so can't capture the logs with `caplog`
    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_bucket_not_found"


@mock_s3  # type: ignore
def test_read_key_not_found(capsys: CaptureFixture[str]) -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    with pytest.raises(botocore.exceptions.ClientError):
        read("s3://testbucket/test.file")

    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_key_not_found"


@mock_s3  # type: ignore
def test_exists() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is True


@mock_s3  # type: ignore
def test_directory_exists() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="hello/test.file", Body=b"test content")

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
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is False


@mock_s3  # type: ignore
def test_exists_object_starting_with_not_exists() -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/hello/another.fi")

    assert file_exists is False
