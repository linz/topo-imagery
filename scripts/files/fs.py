from scripts.aws.aws_helper import is_s3
from scripts.files import fs_local, fs_s3


def write(destination: str, source: bytes) -> None:
    if is_s3(destination):
        fs_s3.write(destination, source)
    else:
        fs_local.write(destination, source)


def read(path: str) -> bytes:
    if is_s3(path):
        return fs_s3.read(path)

    return fs_local.read(path)
