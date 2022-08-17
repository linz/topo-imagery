import os


def get_file_name_from_path(path: str) -> str:
    filename, _ = os.path.splitext(os.path.basename(path))
    return filename


def strip_extension(file: str) -> str:
    if file.endswith("tiff"):
        return file.rstrip(".tiff")
    return file.rstrip(".tif")


def is_tiff(path: str) -> bool:
    return path.lower().endswith((".tiff", ".tif"))
