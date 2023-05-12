import os


def get_file_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def is_tiff(path: str) -> bool:
    return path.lower().endswith((".tiff", ".tif"))


def is_vrt(path: str) -> bool:
    return path.lower().endswith(".vrt")


def is_json(path: str) -> bool:
    return path.lower().endswith(".json")
