import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import ulid
from linz_logger import get_log

from scripts.aws.aws_helper import is_s3
from scripts.files import fs_local, fs_s3


def write(destination: str, source: bytes) -> None:
    """Write a file from its source to a destination path.

    Args:
        destination: A path to where the file will be written.
        source: The source file in bytes.
    """
    if is_s3(destination):
        fs_s3.write(destination, source)
    else:
        fs_local.write(destination, source)


def read(path: str) -> bytes:
    """Read a file from its path.

    Args:
        path: A path to a file to read.

    Returns:
        bytes: The bytes content of the file.
    """
    if is_s3(path):
        return fs_s3.read(path)

    return fs_local.read(path)


def exists(path: str) -> bool:
    """Check if path (file or directory) exists.

    Args:
        path: A path to a directory or file

    Returns:
        bool: True if the path exists
    """
    if is_s3(path):
        return fs_s3.exists(path)
    return fs_local.exists(path)


def _download_tiff_and_sidecar(target: str, file: str) -> str:
    """
    Download a tiff file and some of its sidecar files if they exist to the target dir.

    Args:
        target (str): target folder to write to
        s3_file (str): source file

    Returns:
        downloaded file path
    """
    download_path = os.path.join(target, f"{ulid.ULID()}.tiff")
    get_log().info("Download File", path=file, target_path=download_path)
    write(download_path, read(file))
    for ext in [".prj", ".tfw"]:
        try:
            fs_local.write(f"{target.split('.')[0]}{ext}", read(f"{file.split('.')[0]}{ext}"))
            get_log().info(
                "Download tiff sidecars", path=f"{file.split('.')[0]}{ext}", target_path=f"{target.split('.')[0]}{ext}"
            )
        except:  # pylint: disable-msg=bare-except
            pass
    return download_path


def download_files_parallel_multithreaded(inputs: List[str], target: str, concurrency: int = 10) -> List[str]:
    """
    Download list of files to target destination using multithreading.

    Args:
        inputs (list): list of files to download
        target (str): target folder to write to


    Returns:
        list of downloaded file paths
    """
    downloaded_tiffs: List[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futuress = {executor.submit(_download_tiff_and_sidecar, target, input): input for input in inputs}
        for future in as_completed(futuress):
            if future.exception():
                get_log().warn("Failed Download", error=future.exception())
            else:
                downloaded_tiffs.append(future.result())
    return downloaded_tiffs
