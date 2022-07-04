import file_s3 as fss3
import fsspec

fs = fsspec.filesystem(protocol=None)


def write(destination_path: str, source: str, recursive: bool = False) -> None:
    """Write a file to a destination path.

    Args:
        destination_path (str): The file path to write
        source (str): The source file (path,...)
    """
    if fss3.is_s3_path(destination_path):
        fss3.write(destination_path, source, recursive)
    else:
        fs.copy(source, destination_path)
