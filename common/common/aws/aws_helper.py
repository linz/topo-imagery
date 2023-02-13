import json
from dataclasses import dataclass
from os import environ
from time import sleep
from typing import Any, Dict, List, NamedTuple, Optional
from urllib.parse import urlparse

import boto3
import botocore
from botocore.credentials import AssumeRoleCredentialFetcher, DeferredRefreshableCredentials
from linz_logger import get_log

from common.aws.aws_credential_source import CredentialSource

S3Path = NamedTuple("S3Path", [("bucket", str), ("key", str)])

aws_profile = environ.get("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile)
sessions: Dict[str, boto3.Session] = {}

bucket_roles: List[CredentialSource] = []

client_sts = session.client("sts")

bucket_config_path = environ.get("AWS_ROLE_CONFIG_PATH", "s3://linz-bucket-config/config.json")


# Load bucket to roleArn mapping for LINZ internal buckets from SSM
def _init_roles() -> None:
    s3 = session.resource("s3")
    config_path = parse_path(bucket_config_path)
    content_object = s3.Object(config_path.bucket, config_path.key)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    json_content = json.loads(file_content)

    get_log().trace("bucket_config_load", config=bucket_config_path)

    for cfg in json_content["prefixes"]:
        bucket_roles.append(CredentialSource(**cfg))

    get_log().debug("bucket_config_loaded", config=bucket_config_path, prefix_count=len(bucket_roles))


def _get_client_creator(local_session: boto3.Session) -> Any:
    def client_creator(service_name: str, **kwargs: Any) -> Any:
        return local_session.client(service_name, **kwargs)

    return client_creator


def get_session(prefix: str) -> boto3.Session:
    cfg = _get_credential_config(prefix)
    if cfg is None:
        raise Exception(f"Unable to find role for prefix: {prefix}")

    current_session = sessions.get(cfg.roleArn, None)
    if current_session is not None:
        return current_session

    extra_args: Dict[str, Any] = {"DurationSeconds": cfg.roleSessionDuration}

    if cfg.externalId:
        extra_args["ExternalId"] = cfg.externalId

    fetcher = AssumeRoleCredentialFetcher(
        client_creator=_get_client_creator(session),
        source_credentials=session.get_credentials(),
        role_arn=cfg.roleArn,
        extra_args=extra_args,
    )
    botocore_session = botocore.session.Session()

    # pylint:disable=protected-access
    botocore_session._credentials = DeferredRefreshableCredentials(
        method="assume-role", refresh_using=fetcher.fetch_credentials
    )

    current_session = boto3.Session(botocore_session=botocore_session)
    sessions[cfg.roleArn] = current_session

    get_log().info("role_assume", prefix=prefix, bucket=cfg.bucket, role_arn=cfg.roleArn)
    return current_session


@dataclass
class AwsFrozenCredentials:
    """
    work around as I couldn't find the type for get_frozen_credentials()
    """

    access_key: str
    secret_key: str
    token: str


def get_session_credentials(prefix: str, retry_count: int = 3) -> AwsFrozenCredentials:
    """
    Attempt to get credentials for a prefix, retrying upto retry_count amount of times
    """
    last_error: Exception = Exception(f"Invalid retry count: {retry_count}")
    for retry in range(1, retry_count + 1):
        try:
            # Get credentials may give differing access_key and secret_key
            credentials: AwsFrozenCredentials = get_session(prefix).get_credentials().get_frozen_credentials()
            return credentials
        except client_sts.exceptions.InvalidIdentityTokenException as e:
            get_log().warn("bucket_load_retry", retry_count=retry)
            sleep(0.5 * retry)
            last_error = e

    raise last_error


def _get_credential_config(prefix: str) -> Optional[CredentialSource]:
    get_log().debug("get_credentials_bucket_name", prefix=prefix)
    if not bucket_roles:
        _init_roles()

    for cfg in bucket_roles:
        if prefix.startswith(cfg.prefix):
            return cfg

    return None


def parse_path(path: str) -> S3Path:
    """Parse the path and split it into bucket name and key.

    Args:
        path (str): A S3 path.

    Returns:
        S3Path (NamedTuple): s3_path.bucket (str), s3_path.key (str)
    """
    parse = urlparse(path, allow_fragments=False)
    return S3Path(parse.netloc, parse.path[1:])


def is_s3(path: str) -> bool:
    return path.startswith("s3://")
