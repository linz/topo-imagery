import json

from boto3 import client, resource
from botocore.exceptions import ClientError
from moto import mock_aws
from moto.core.models import DEFAULT_ACCOUNT_ID
from moto.s3.models import s3_backends
from moto.s3.responses import DEFAULT_REGION_NAME
from moto.wafv2.models import GLOBAL_REGION
from mypy_boto3_s3 import S3Client
from pytest import CaptureFixture, raises
from pytest_subtests import SubTests

from scripts.files.files_helper import ContentType
from scripts.files.fs_s3 import exists, list_files_in_uri, modified, read, write
from scripts.tests.datetimes_test import any_epoch_datetime


@mock_aws
def test_write(subtests: SubTests) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.file", b"test content")

    resp = boto3_client.get_object(Bucket="testbucket", Key="test.file")
    with subtests.test():
        assert resp["Body"].read() == b"test content"

    with subtests.test():
        assert resp["ContentType"] == "binary/octet-stream"


@mock_aws
def test_write_content_type(subtests: SubTests) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write("s3://testbucket/test.tiff", b"test content", ContentType.GEOTIFF.value)
    resp = boto3_client.get_object(Bucket="testbucket", Key="test.tiff")
    with subtests.test():
        assert resp["Body"].read() == b"test content"

    with subtests.test():
        assert resp["ContentType"] == ContentType.GEOTIFF.value


@mock_aws
def test_read() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    content = read("s3://testbucket/test.file")

    assert content == b"test content"


@mock_aws
def test_read_bucket_not_found(capsys: CaptureFixture[str]) -> None:
    with raises(ClientError):
        read("s3://testbucket/test.file")

    # python-linz-logger uses structlog which doesn't use stdlib so can't capture the logs with `caplog`
    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_bucket_not_found"


@mock_aws
def test_read_key_not_found(capsys: CaptureFixture[str]) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    with raises(ClientError):
        read("s3://testbucket/test.file")

    logs = json.loads(capsys.readouterr().out)
    assert logs["msg"] == "s3_key_not_found"


@mock_aws
def test_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="test.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is True


@mock_aws
def test_directory_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/test.file", Body=b"test content")

    directory_exists = exists("s3://testbucket/hello/")

    assert directory_exists is True


@mock_aws
def test_exists_bucket_not_exists(capsys: CaptureFixture[str], subtests: SubTests) -> None:
    file_exists = exists("s3://testbucket/test.file")

    logs = json.loads(capsys.readouterr().out)
    with subtests.test():
        assert logs["msg"] == "s3_bucket_not_found"

    with subtests.test():
        assert file_exists is False


@mock_aws
def test_exists_object_not_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/test.file")

    assert file_exists is False


@mock_aws
def test_exists_object_starting_with_not_exists() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")
    boto3_client.put_object(Bucket="testbucket", Key="hello/another.file", Body=b"test content")

    file_exists = exists("s3://testbucket/hello/another.fi")

    assert file_exists is False


@mock_aws
def test_list_files_in_uri(subtests: SubTests) -> None:
    bucket_name = "testbucket"
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket=bucket_name)
    boto3_client.put_object(Bucket=bucket_name, Key="data/collection.json", Body=b"")
    boto3_client.put_object(Bucket=bucket_name, Key="data/image.tiff", Body=b"")
    boto3_client.put_object(Bucket=bucket_name, Key="data/image_meta.xml", Body=b"")

    files = list_files_in_uri(f"s3://{bucket_name}/data/", [".json", "_meta.xml"], boto3_client)

    with subtests.test():
        assert len(files) == 2

    with subtests.test():
        assert set(files) == {"data/collection.json", "data/image_meta.xml"}

    with subtests.test():
        assert "data/image.tiff" not in files


@mock_aws
def test_should_get_modified_datetime() -> None:
    bucket_name = "any-bucket-name"
    key = "any-key"
    modified_datetime = any_epoch_datetime()

    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket=bucket_name)
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"any body")
    s3_backends[DEFAULT_ACCOUNT_ID][GLOBAL_REGION].buckets[bucket_name].keys[key].last_modified = modified_datetime

    assert modified(bucket_name, key, s3_client) == modified_datetime
