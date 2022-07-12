import boto3
import botocore
from aws_helper import get_bucket_name_from_path, get_credentials, parse_path
from fs_local import write as local_write
from s3fs import S3FileSystem

fs_s3 = S3FileSystem(anon=False)


def is_s3_path(path: str) -> bool:
    if path:
        return path.startswith("s3://")
    return False


def write(destination_path: str, source: str, recursive: bool = False) -> None:
    if is_s3_path(source):
        tmp_file_path = "tmp.file"
        local_write(tmp_file_path, read(source))
        source = tmp_file_path
    try:
        fs_s3.put(source, destination_path, recursive=recursive)
    except PermissionError:fs_s3.secret = credentials.secret_key
        fs_s3.token = credentials.token
        fs_s3.key = credentials.access_keytials(get_bucket_name_from_path(destination_path))
        fs_s3.secret = credentials.secret_key
        fs_s3.token = credentials.token
        fs_s3.key = credentials.access_key
        write(destination_path, source, recursive)


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


def main() -> None:
    write(
        "s3://paniertest/files/my_file.tif",
        "s3://linz-imagery-staging/RGBi4/tasman_rural_2020_0.3m_a_RGBI/tif/2020_BQ24_5000_0601.tif",
    )


if __name__ == "__main__":
    main()
