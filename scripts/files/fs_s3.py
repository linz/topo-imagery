from typing import TYPE_CHECKING, Dict

import boto3
import botocore
from linz_logger import get_log

from scripts.aws.aws_helper import get_credentials, parse_path

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import S3ServiceResource
else:
    S3ServiceResource = object

# s3_session = [{"bucket", boto3.Session}]
s3_sessions: Dict[str, S3ServiceResource] = {}


def _get_s3_resource(bucket_name: str) -> S3ServiceResource:
    """Return a boto3 S3 Resource with the AWS credentials for a bucket.

    Args:
        bucket_name (str): The name of the bucket.

    Returns:
        S3ServiceResource: The boto3 S3 Resource.
    """
    session = s3_sessions.get(bucket_name, None)
    if session is None:
        # TODO implement refreshable session TDE-235
        credentials = get_credentials(bucket_name)
        session = boto3.Session(
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.token,
        )
    s3_sessions[bucket_name] = session

    s3: S3ServiceResource = session.resource("s3")
    return s3


def write(destination: str, source: bytes, needs_credentials: bool = False) -> None:
    """Write a source (bytes) in a AWS s3 destination (path in a bucket).

    Args:
        destination (str): The AWS S3 path to the file to write.
        source (bytes): The source file in bytes.
        needs_credentials (bool, optional): Tells if credentials are needed. Defaults to False.
    """
    if source is None:
        get_log().error("write_s3_source_none", path=destination, error="The 'source' is None.")
        raise Exception("The 'source' is None.")
    s3_path = parse_path(destination)
    key = s3_path.key

    if needs_credentials:
        s3 = _get_s3_resource(s3_path.bucket)
    else:
        s3 = boto3.resource("s3")

    try:
        s3_object = s3.Object(s3_path.bucket, key)
        s3_object.put(Body=source)
        # TODO add the duration
        get_log().debug("write_s3_success", path=destination)
    except botocore.exceptions.ClientError as ce:
        # Boto3 Resources exceptions are not exposed like for Clients
        if not needs_credentials and ce.response["Error"]["Code"] == "AccessDenied":
            write(destination, source, True)

        get_log().error("write_s3_error", path=destination, error=f"Unable to write the file: {ce}")
        raise ce


def read(path: str, needs_credentials: bool = False) -> bytes:
    """Read a file on a AWS S3 bucket.

    Args:
        path (str): The AWS S3 path to the file to read.
        needs_credentials (bool, optional):  Tells if credentials are needed. Defaults to False.

    Returns:
        bytes: The file in bytes.
    """
    s3_path = parse_path(path)
    key = s3_path.key
    s3 = boto3.resource("s3")

    try:
        if needs_credentials:
            s3 = _get_s3_resource(s3_path.bucket)

        s3_object = s3.Object(s3_path.bucket, key)
        file: bytes = s3_object.get()["Body"].read()
    except botocore.exceptions.ClientError as ce:
        if not needs_credentials and ce.response["Error"]["Code"] == "AccessDenied":
            get_log().debug("read_s3_needs_credentials", path=path)
            return read(path, True)
        if ce.response["Error"]["Code"] == "NoSuchBucket":
            get_log().error("read_s3_bucket_not_found", path=path, error=f"The specified bucket does not seem to exist: {ce}")
        if ce.response["Error"]["Code"] == "NoSuchKey":
            get_log().error("read_s3_file_not_found", path=path, error=f"The specified file does not seem to exist: {ce}")

        get_log().error("read_s3_error", path=path, error=f"Unable to read the file: {ce}")
        raise ce
    # TODO add the duration
    get_log().debug("read_s3_success", path=path)
    return file
