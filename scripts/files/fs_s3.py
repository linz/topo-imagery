from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Generator, List, Optional, Union

import boto3
import botocore
from linz_logger import get_log

from scripts.aws.aws_helper import get_session, parse_path
from scripts.files.files_helper import is_json
from scripts.logging.time_helper import time_in_ms


def write(destination: str, source: bytes) -> None:
    """Write a source (bytes) in a AWS s3 destination (path in a bucket).

    Args:
        destination (str): The AWS S3 path to the file to write.
        source (bytes): The source file in bytes.
    """
    start_time = time_in_ms()
    if source is None:
        get_log().error("write_s3_source_none", path=destination, error="The 'source' is None.")
        raise Exception("The 'source' is None.")
    s3_path = parse_path(destination)
    key = s3_path.key
    s3 = boto3.resource("s3")

    try:
        s3_object = s3.Object(s3_path.bucket, key)
        s3_object.put(Body=source)
        get_log().debug("write_s3_success", path=destination, duration=time_in_ms() - start_time)
    except botocore.exceptions.ClientError as ce:
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
    start_time = time_in_ms()
    s3_path = parse_path(path)
    key = s3_path.key
    s3 = boto3.resource("s3")

    try:
        if needs_credentials:
            s3 = get_session(path).resource("s3")

        s3_object = s3.Object(s3_path.bucket, key)
        file: bytes = s3_object.get()["Body"].read()
    except s3.meta.client.exceptions.ClientError as ce:
        if not needs_credentials and ce.response["Error"]["Code"] == "AccessDenied":
            get_log().debug("read_s3_needs_credentials", path=path)
            return read(path, True)
        raise ce
    except s3.meta.client.exceptions.NoSuchBucket as nsb:
        get_log().error("read_s3_bucket_not_found", path=path, error=f"The specified bucket does not seem to exist: {nsb}")
        raise nsb
    except s3.meta.client.exceptions.NoSuchKey as nsk:
        get_log().error("read_s3_file_not_found", path=path, error=f"The specified file does not seem to exist: {nsk}")
        raise nsk

    get_log().debug("read_s3_success", path=path, duration=time_in_ms() - start_time)
    return file


def bucket_name_from_path(path: str) -> str:
    path_parts = path.replace("s3://", "").split("/")
    return path_parts.pop(0)


def prefix_from_path(path: str) -> str:
    bucket_name = bucket_name_from_path(path)
    return path.replace(f"s3://{bucket_name}/", "")


def list_json_in_uri(uri: str, s3_client: Optional[boto3.client]) -> List[str]:
    if not s3_client:
        s3_client = boto3.client("s3")
    files = []
    paginator = s3_client.get_paginator("list_objects_v2")
    response_iterator = paginator.paginate(Bucket=bucket_name_from_path(uri), Prefix=prefix_from_path(uri))

    for response in response_iterator:
        for contents_data in response["Contents"]:
            key = contents_data["Key"]
            if not is_json(key):
                get_log().trace("skipping file not json", file=key, action="collection_from_items", reason="skip")
                continue
            files.append(key)
    get_log().info("Files Listed", number_of_files=len(files))
    return files


def _get_object(bucket: str, file_name: str, s3_client: boto3.client) -> Any:
    get_log().info("Retrieving File", path=f"s3://{bucket}/{file_name}")
    return s3_client.get_object(Bucket=bucket, Key=file_name)


def get_object_parallel_multithreading(
    bucket: str, files_to_read: List[str], s3_client: Optional[boto3.client], concurrency: int
) -> Generator[Any, Union[Any, BaseException], None]:
    if not s3_client:
        s3_client = boto3.client("s3")
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_key = {executor.submit(_get_object, bucket, key, s3_client): key for key in files_to_read}

        for future in futures.as_completed(future_to_key):
            key = future_to_key[future]
            exception = future.exception()

            if not exception:
                yield key, future.result()
            else:
                yield key, exception
