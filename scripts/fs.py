from typing import List, Optional, Tuple

import fs_local
import fs_s3
from aws_helper import is_s3


def write(destination: str, source: bytes) -> None:
    if is_s3(destination):
        fs_s3.write(destination, source)
    else:
        fs_local.write(destination, source)


def read(path: str) -> bytes:
    if is_s3(path):
        return fs_s3.read(path)

    return fs_local.read(path)


def scandir(directory: str, extensions: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    if is_s3(directory):
        return fs_s3.scandir(directory, extensions)
    return fs_local.scandir(directory, extensions)
