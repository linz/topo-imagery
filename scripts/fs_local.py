def write(destination_path: str, source: bytes) -> None:
    """Write a file to a destination path.

    Args:
        destination_path (str): The file path to write
        source (str): The source file (path,...)
    """
    with open(destination_path, "wb") as buffer:
        buffer.write(source)


def read(path: str):
    # Check protocol
    # if s3 download the file
    with open(path, "rb") as buffer:
        return buffer.read()


def list(path: str):
    pass


if __name__ == "__main__":
    print("test")
    write("aws_helper.bak", read("scripts/aws_helper.py"))
