import os


def get_file_name_from_path(path: str) -> str:
    return os.path.basename(path)


def is_tiff(path: str) -> bool:
    return path.lower().endswith((".tiff", ".tif"))
