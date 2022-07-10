import boto3
from aws_helper import get_bucket_name_from_path, get_credentials, parse_path
from s3fs import S3FileSystem

fs_s3 = S3FileSystem(anon=False)


def is_s3_path(path: str) -> bool:
    if path:
        return path.startswith("s3://")
    return False


def write(destination_path: str, source: str, recursive: bool = False) -> None:
    try:
        fs_s3.put(source, destination_path, recursive=recursive)
    except PermissionError:
        credentials = get_credentials(get_bucket_name_from_path(destination_path))
        fs_s3.secret = credentials.secret_key
        fs_s3.token = credentials.token
        fs_s3.key = credentials.access_key
        write(destination_path, source, recursive)


def read(path: str) -> bytes:
    bucket_name, key = parse_path(path)
    s3 = boto3.resource("s3")
    try:
        s3_object = s3.Object(bucket_name, key)
    except PermissionError:
        credentials = get_credentials(bucket_name)
        fs_s3.secret = credentials.secret_key
        fs_s3.token = credentials.token
        fs_s3.key = credentials.access_key
        session = boto3.Session(
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.token,
        )
        s3 = session.resource("s3")
        s3_object = s3.Object(bucket_name, key)

    return s3_object.get()["Body"].read().decode("utf-8")
