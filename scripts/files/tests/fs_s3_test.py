import boto3
import botocore
import pytest
from moto import mock_s3
from moto.s3.responses import DEFAULT_REGION_NAME
from pytest import CaptureFixture

from scripts.files.fs_s3 import FsS3Exception, read, rename, write


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
        sysout = capsys.readouterr()
        assert "read_s3_bucket_not_found" in sysout.out


@mock_s3  # type: ignore
def test_read_file_not_found(capsys: CaptureFixture[str]) -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    with pytest.raises(botocore.exceptions.ClientError):
        read("s3://testbucket/test.file")
        sysout = capsys.readouterr()
        assert "read_s3_file_not_found" in sysout.out


@mock_s3  # type: ignore
def test_rename(capsys: CaptureFixture[str]) -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")
    src_path = "s3://testbucket/test.file"
    dst_path = "s3://testbucket/testB.file"
    rename(src_path, dst_path)

    with pytest.raises(botocore.exceptions.ClientError):
        read("s3://testbucket/test.file")
        sysout = capsys.readouterr()
        assert "read_s3_file_not_found" in sysout.out

    content = read("s3://testbucket/testB.file")

    assert content == b"test content"


@mock_s3  # type: ignore
def test_rename_different_bucket(capsys: CaptureFixture[str]) -> None:
    s3 = boto3.resource("s3", region_name=DEFAULT_REGION_NAME)
    client = boto3.client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")
    src_path = "s3://testbucket/test.file"
    dst_path = "s3://testbucket2/testB.file"

    with pytest.raises(FsS3Exception):
        rename(src_path, dst_path)
        read("s3://testbucket/test.file")
        sysout = capsys.readouterr()
        assert "rename_s3_different_buckets" in sysout.out
