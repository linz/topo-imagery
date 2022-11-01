import boto3
import botocore
from linz_logger import get_log

from scripts.aws.aws_helper import get_session, parse_path
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
            s3 = get_session(path).client("s3")

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


def rename(path: str, new_path: str, needs_credentials: bool = False) -> None:
    """'Rename' an s3 object: copy an existing object to another with the new key name and delete the old object.
        The objects have to be in the same bucket.

    Args:
        path (str): the path of the object to rename.
        new_path (str): the path with the new name.
        needs_credentials (bool, optional): Tells if credentials are needed. Defaults to False.

    Raises:
        Exception: an exception if the path are not in the same bucket
        ce: a client exception
        nsb: a no such bucket exception
        nsk: a no such key exception
    """
    start_time = time_in_ms()
    src_s3_path = parse_path(path)
    dst_s3_path = parse_path(new_path)

    if src_s3_path.bucket != dst_s3_path.bucket:
        get_log().error(
            "rename_s3_different_buckets",
            path=path,
            destination=new_path,
            error="The source and destination path are not in the same bucket",
        )
        raise Exception(f"Files {path} and {new_path} are not on the same S3 bucket.")

    s3 = boto3.resource("s3")
    try:
        if needs_credentials:
            s3 = get_session(path).client("s3")

        dst_s3_object = s3.Object(dst_s3_path.bucket, dst_s3_path.key)
        src_s3_object = s3.Object(src_s3_path.bucket, src_s3_path.key)
        try:
            # check if the original file exists
            src_s3_object.load()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                get_log().error(
                    "rename_s3_not_exists",
                    path=path,
                    destination=new_path,
                    error="The file to rename does not exist.",
                )
            raise Exception(f"{path} does not exists.") from e

        try:
            # check if the destination file already exists
            dst_s3_object.load()
            get_log().error(
                "rename_s3_already_exists",
                path=path,
                destination=new_path,
                error="A file for the destination path already exists.",
            )
            raise Exception(f"{new_path} already exists. The file can't be renamed with this path.")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # OK: the destination file does not already exists
                dst_s3_object.copy({"Bucket": src_s3_path.bucket, "Key": src_s3_path.key})
                # delete the source
                src_s3_object = s3.Object(src_s3_path.bucket, src_s3_path.key)
                src_s3_object.delete()
                get_log().debug("rename_s3_success", path=path, destination=new_path, duration=time_in_ms() - start_time)
    except s3.meta.client.exceptions.ClientError as ce:
        if not needs_credentials and ce.response["Error"]["Code"] == "AccessDenied":
            get_log().debug("rename_s3_needs_credentials", path=path, destination=new_path)
            return rename(path, new_path, True)
        raise ce
    except s3.meta.client.exceptions.NoSuchBucket as nsb:
        get_log().error(
            "rename_s3_bucket_not_found",
            path=path,
            destination=new_path,
            error=f"The specified bucket does not seem to exist: {nsb}",
        )
        raise nsb
    except s3.meta.client.exceptions.NoSuchKey as nsk:
        get_log().error(
            "rename_s3_file_not_found",
            path=path,
            destination=new_path,
            error=f"The specified file does not seem to exist: {nsk}",
        )
        raise nsk
    return None


def bucket_name_from_path(path: str) -> str:
    path_parts = path.replace("s3://", "").split("/")
    return path_parts.pop(0)


def prefix_from_path(path: str) -> str:
    bucket_name = bucket_name_from_path(path)
    return path.replace(f"s3://{bucket_name}/", "")
