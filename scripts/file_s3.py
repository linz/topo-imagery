from aws_helper import get_bucket_name_from_path, get_credentials
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
