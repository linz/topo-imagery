from typing import List, Optional, Tuple

import boto3
import botocore
from aws_helper import get_credentials, parse_path
from linz_logger import get_log


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
        get_log().info("write_s3_success", path=destination, response=response)
    else:
        get_log().error("write_s3_error", path=destination, response=response)


def read(path: str) -> bytes:
    bucket_name, key = parse_path(path)
    key = key[1:]
    s3 = boto3.resource("s3")
    try:
        s3_object = s3.Object(bucket_name, key)
        file = s3_object.get()["Body"].read()
    except botocore.exceptions.ClientError:
        credentials = get_credentials(bucket_name)
        session = boto3.Session(
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.token,
        )
        s3 = session.resource("s3")
        s3_object = s3.Object(bucket_name, key)
        file = s3_object.get()["Body"].read()

    return file


def scandir(directory: str, extensions: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    pass
