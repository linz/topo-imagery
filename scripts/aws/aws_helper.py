import json
from os import environ
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import urlparse

import boto3
from linz_logger import get_log

from scripts.logging.logging_keys import LOG_REASON_START, LOG_REASON_SUCCESS
from scripts.logging.time_helper import time_in_ms

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket
else:
    Bucket = object

Credentials = NamedTuple("Credentials", [("access_key", str), ("secret_key", str), ("token", str)])
S3Path = NamedTuple("S3Path", [("bucket", str), ("key", str)])

aws_profile = environ.get("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile)
bucket_roles = {}
bucket_credentials = {}
client_sts = session.client("sts")

# Load bucket to roleArn mapping for LINZ internal buckets from SSM
def init_roles() -> None:
    start_time = time_in_ms()
    bucket_config_name = "linz-bucket-config"
    config_name = "config.json"
    config_path = f"s3://{bucket_config_name}/{config_name}"

    get_log().debug(
        "Retrieving AWS roles started",
        action=init_roles.__name__,
        reason=LOG_REASON_START,
        path=config_path,
        aws={"action": "get", "bucket": bucket_config_name, "object": config_name, "service": "s3"},
    )

    s3 = boto3.resource("s3")

    content_object = s3.Object(bucket_config_name, config_name)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    json_content = json.loads(file_content)

    for cfg in json_content["buckets"]:
        bucket_roles[cfg["bucket"]] = cfg

    get_log().debug(
        "Retrieving AWS roles ended",
        action=init_roles.__name__,
        reason=LOG_REASON_SUCCESS,
        path=config_path,
        content=json_content,
        duration=time_in_ms() - start_time,
    )


def get_credentials(bucket_name: str) -> Credentials:
    start_time = time_in_ms()
    get_log().debug(
        f"Getting AWS credentials for bucket: '{bucket_name}' started",
        action=get_credentials.__name__,
        reason=LOG_REASON_START,
        parameters={"bucket_name": bucket_name},
    )

    if not bucket_roles:
        init_roles()
    if bucket_name in bucket_roles:
        # FIXME: check if the token is expired - add a parameter
        if bucket_name not in bucket_credentials:
            role_arn = bucket_roles[bucket_name]["roleArn"]
            get_log().debug(
                f"Assuming AWS ARN Role for bucket: {bucket_name}",
                action=get_credentials.__name__,
                aws={"action": "assume_role", "bucket": bucket_name, "roleArn": role_arn, "service": "sts"},
            )
            assumed_role_object = client_sts.assume_role(RoleArn=role_arn, RoleSessionName="gdal")
            bucket_credentials[bucket_name] = Credentials(
                assumed_role_object["Credentials"]["AccessKeyId"],
                assumed_role_object["Credentials"]["SecretAccessKey"],
                assumed_role_object["Credentials"]["SessionToken"],
            )
        get_log().debug(
            f"Getting AWS credentials for bucket: '{bucket_name}' ended",
            action=get_credentials.__name__,
            reason=LOG_REASON_SUCCESS,
            parameters={"bucket_name": bucket_name},
            duration=time_in_ms() - start_time,
        )
        return bucket_credentials[bucket_name]

    session_credentials = session.get_credentials()
    default_credentials = Credentials(
        session_credentials.access_key, session_credentials.secret_key, session_credentials.token
    )

    get_log().debug(
        f"Using default credentials for bucket: '{bucket_name}'",
        action=get_credentials.__name__,
        reason=LOG_REASON_SUCCESS,
        parameters={"bucket_name": bucket_name},
        duration=time_in_ms() - start_time,
    )
    return default_credentials


def get_bucket(bucket_name: str) -> Bucket:
    start_time = time_in_ms()
    get_log().debug(
        f"Getting AWS Bucket S3 resource for bucket: '{bucket_name}' started",
        action=get_bucket.__name__,
        reason=LOG_REASON_START,
        parameters={"bucket_name": bucket_name},
    )
    credentials = get_credentials(bucket_name=bucket_name)

    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )
    s3_bucket: Bucket = s3_resource.Bucket(bucket_name)

    get_log().debug(
        f"Getting AWS Bucket S3 resource for bucket: '{bucket_name}' ended",
        action=get_bucket.__name__,
        reason=LOG_REASON_SUCCESS,
        parameters={"bucket_name": bucket_name},
        duration=time_in_ms() - start_time,
    )
    return s3_bucket


def get_bucket_name_from_path(path: str) -> str:
    path_parts = path.replace("s3://", "").split("/")
    return path_parts.pop(0)


def parse_path(path: str) -> S3Path:
    """Parse the path and split it into bucket name and key.

    Args:
        path (str): A S3 path.

    Returns:
        S3Path (NamedTupe): s3_path.bucket (str), s3_path.key (str)
    """
    parse = urlparse(path, allow_fragments=False)
    return S3Path(parse.netloc, parse.path[1:])


def is_s3(path: str) -> bool:
    return path.startswith("s3://")
