import os
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

from boto3 import client, resource
from moto import mock_aws
from moto.core.models import DEFAULT_ACCOUNT_ID
from moto.s3.models import s3_backends
from moto.s3.responses import DEFAULT_REGION_NAME
from moto.wafv2.models import GLOBAL_REGION
from mypy_boto3_s3 import S3Client
from pytest import CaptureFixture, raises
from pytest_subtests import SubTests

from scripts.files.fs import NoSuchFileError, modified, read, write, write_all, write_sidecars
from scripts.tests.datetimes_test import any_modern_datetime


def test_read_key_not_found_local() -> None:
    with raises(NoSuchFileError):
        read("test_dir/test.file")


@mock_aws
def test_read_key_not_found_s3(capsys: CaptureFixture[str]) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    with raises(NoSuchFileError):
        read("s3://testbucket/test.file")

    assert "s3_key_not_found" in capsys.readouterr().out


def test_write_all_file_not_found_local() -> None:
    # Raises an exception as all files are not writte·
    with raises(Exception) as e:
        write_all(["/test.prj"], "/tmp")

    assert str(e.value) == "Not all mandatory source files were written"


def test_write_sidecars_file_not_found_local(capsys: CaptureFixture[str]) -> None:
    write_sidecars(["/test.prj"], "/tmp")
    assert "No sidecar file found; skipping" in capsys.readouterr().out


@mock_aws
def test_write_all_key_not_found_s3() -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    # Raises an exception as all files are not written
    with raises(Exception) as e:
        write_all(["s3://testbucket/test.tif"], "/tmp")

    assert str(e.value) == "Not all mandatory source files were written"


@mock_aws
def test_write_sidecars_key_not_found_s3(capsys: CaptureFixture[str]) -> None:
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="testbucket")

    write_sidecars(["s3://testbucket/test.prj"], "/tmp")

    # capsys.readouterr().out json string format is not valid which implies
    # we can't parse it to find the actual `msg`
    assert "No sidecar file found; skipping" in capsys.readouterr().out


def test_write_sidecars_one_found(capsys: CaptureFixture[str], subtests: SubTests) -> None:
    target = mkdtemp()
    # Add a file to read
    content = b"test content"
    path = os.path.join(target, "test.tfw")
    write(path, content)
    non_existing_path = os.path.join(target, "test.prj")
    # Write the sidecar files with one unexisting
    write_sidecars([non_existing_path, path], os.path.join(target, "/tmp"))
    logs = capsys.readouterr().out
    with subtests.test(msg="One has not been found"):
        assert "No sidecar file found; skipping" in logs

    with subtests.test(msg="One has been found"):
        assert "wrote_sidecar_file" in logs

    rmtree(target)


@mock_aws
def test_should_get_s3_object_modified_datetime() -> None:
    bucket_name = "any-bucket-name"
    key = "any-key"
    modified_datetime = any_modern_datetime()

    s3_client: S3Client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3_client.create_bucket(Bucket=bucket_name)
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"any body")
    s3_backends[DEFAULT_ACCOUNT_ID][GLOBAL_REGION].buckets[bucket_name].keys[key].last_modified = modified_datetime

    assert modified(f"s3://{bucket_name}/{key}", s3_client) == modified_datetime


def test_should_get_local_file_modified_datetime(setup: str) -> None:
    path = os.path.join(setup, "modified.file")
    Path(path).touch()
    modified_datetime = any_modern_datetime()
    os.utime(path, times=(any_modern_datetime().timestamp(), modified_datetime.timestamp()))
    assert modified(path) == modified_datetime
