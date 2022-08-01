from typing import TYPE_CHECKING

import boto3
import botocore
from linz_logger import get_log

from scripts.aws.aws_helper import get_credentials, parse_path

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import S3ServiceResource
else:
    S3ServiceResource = object


def get_auth_s3_session(bucket_name: str) -> S3ServiceResource:
    credentials = get_credentials(bucket_name)
    session = boto3.Session(
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )
    s3: S3ServiceResource = session.resource("s3")
    return s3


def write(destination: str, source: bytes, needs_credentials: bool = False) -> None:
    bucket_name, key = parse_path(destination)
    key = key[1:]
    s3 = boto3.resource("s3")
    try:
        if needs_credentials:
            s3 = get_auth_s3_session(bucket_name)

        s3_object = s3.Object(bucket_name, key)
        response = s3_object.put(Body=source)
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            get_log().debug("write_s3_success", path=destination, response=response)
        else:
            get_log().error("write_s3_error", path=destination, response=response)
    except botocore.exceptions.ClientError as ce:
        if not needs_credentials:
            get_log().debug("write_s3_needs_credentials", path=destination)
            write(destination, source, True)
        else:
            get_log().error("write_s3_error", path=destination, error=f"Unable to write the file: {ce}")


def read(path: str, needs_credentials: bool = False) -> bytes | None:
    bucket_name, key = parse_path(path)
    key = key[1:]
    s3 = boto3.resource("s3")

    try:
        if needs_credentials:
            s3 = get_auth_s3_session(bucket_name)

        s3_object = s3.Object(bucket_name, key)
        file: bytes = s3_object.get()["Body"].read()
    except botocore.exceptions.ClientError as ce:
        if ce.response["Error"]["Code"] == "NoSuchBucket":
            get_log().error("read_s3_bucket_not_found", path=path, error=f"The specified bucket does not seem to exist: {ce}")
            return None
        if ce.response["Error"]["Code"] == "NoSuchKey":
            get_log().error("read_s3_file_not_found", path=path, error=f"The specified file does not seem to exist: {ce}")
            return None
        if not needs_credentials:
            get_log().debug("read_s3_needs_credentials", path=path)
            return read(path, True)

        get_log().error("read_s3_error", path=path, error=f"Unable to read the file: {ce}")
        return None

    get_log().debug("read_s3_success", path=path)
    return file
