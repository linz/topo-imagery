from typing import Optional

import boto3
import botocore
from linz_logger import get_log

from scripts.aws.aws_helper import Credentials, get_credentials, parse_path


def write(destination: str, source: bytes) -> None:
    bucket_name, key = parse_path(destination)
    key = key[1:]
    s3 = boto3.resource("s3")
    try:
        s3_object = s3.Object(bucket_name, key)
        response = s3_object.put(Body=source)
    except botocore.exceptions.ClientError:
        credentials = get_credentials(bucket_name)
        session = boto3.Session(
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.token,
        )
        s3 = session.resource("s3")
        s3_object = s3.Object(bucket_name, key)
        response = s3_object.put(Body=source)

    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        get_log().trace("write_s3_success", path=destination, response=response)
    else:
        get_log().error("write_s3_error", path=destination, response=response)


def read(path: str, need_credentials: bool = True) -> bytes:
    bucket_name, key = parse_path(path)
    key = key[1:]
    s3 = boto3.resource("s3")

    try:
        if need_credentials:
            credentials = get_credentials(bucket_name)
            session = boto3.Session(
                aws_access_key_id=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_session_token=credentials.token,
            )
            s3 = session.resource("s3")

        s3_object = s3.Object(bucket_name, key)
        file = s3_object.get()["Body"].read()
    except botocore.exceptions.ClientError as ce:
        if ce.response["Error"]["Code"] == "NoSuchBucket":
            get_log().error("read_s3_bucket_not_found", path=path, error=f"The specified bucket does not seem to exist: {ce}")
            return None
        if ce.response["Error"]["Code"] == "NoSuchKey":
            get_log().error("read_s3_file_not_found", path=path, error=f"The specified file does not seem to exist: {ce}")
            return None
        if not need_credentials:
            read(path, True)
        get_log().error("read_s3_error", path=path, error=f"Unable to read the file: {ce}")
        return None

    get_log().trace("read_s3_success", path=path)
    return file
