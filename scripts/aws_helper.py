import json
from os import environ
from typing import Any

import boto3
from linz_logger import get_log


class Credentials:
    access_key: str
    secret_key: str
    token: str

    def __init__(self, access_key: str, secret_key: str, token: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token


aws_profile = environ.get("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile)
bucket_roles = {}
bucket_credentials = {}
client_sts = session.client("sts")

# Load bucket to roleArn mapping for LINZ internal buckets from SSM
def init_roles() -> None:
    s3 = boto3.resource("s3")

    content_object = s3.Object("linz-bucket-config", "config.json")
    file_content = content_object.get()["Body"].read().decode("utf-8")
    json_content = json.loads(file_content)

    get_log().debug("bucket_config", config=json_content)

    for cfg in json_content["buckets"]:
        bucket_roles[cfg["bucket"]] = cfg


def get_credentials(bucket_name: str) -> Credentials:
    get_log().debug("get_credentials_bucket_name", bucket_name=bucket_name)
    if not bucket_roles:
        init_roles()
    if bucket_name in bucket_roles:
        # FIXME: check if the token is expired - add a parameter
        if bucket_name not in bucket_credentials:
            role_arn = bucket_roles[bucket_name]["roleArn"]
            get_log().debug("s3_assume_role", bucket_name=bucket_name, role_arn=role_arn)
            assumed_role_object = client_sts.assume_role(RoleArn=role_arn, RoleSessionName="gdal")
            bucket_credentials[bucket_name] = Credentials(
                assumed_role_object["Credentials"]["AccessKeyId"],
                assumed_role_object["Credentials"]["SecretAccessKey"],
                assumed_role_object["Credentials"]["SessionToken"],
            )
        return bucket_credentials[bucket_name]

    session_credentials = session.get_credentials()
    default_credentials = Credentials(
        session_credentials.access_key, session_credentials.secret_key, session_credentials.token
    )

    return default_credentials


def get_bucket(bucket_name: str) -> Any:
    credentials = get_credentials(bucket_name=bucket_name)

    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )

    return s3_resource.Bucket(bucket_name)


def bucket_name_from_path(path: str) -> str:
    path_parts = path.replace("s3://", "").split("/")
    return path_parts.pop(0)
