import os

import pytest
from geoprocessor_common.files.fs_local import copy_file, exists, multihash, read, write

TEST_CONTENT_MULTIHASH = "12206ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"


@pytest.mark.dependency(name="write")
def test_write(setup: str) -> None:
    target = setup
    path = os.path.join(target, "test.file")
    write(path, b"test")
    assert os.path.isfile(path)


def test_write_non_existing_dir(setup: str) -> None:
    target = setup
    path = os.path.join(target, "new_dir/test.file")
    write(path, b"test")
    assert os.path.isfile(path)


@pytest.mark.dependency(name="read", depends=["write"])
def test_read(setup: str) -> None:
    content = b"test content"
    target = setup
    path = os.path.join(target, "test.file")
    write(path, content)
    file_content = read(path)
    assert file_content == content


@pytest.mark.dependency(name="exists", depends=["write"])
def test_exists(setup: str) -> None:
    content = b"test content"
    target = setup
    path = os.path.join(target, "test.file")
    write(path, content)
    found = exists(path)
    assert found is True


def test_exists_file_not_found() -> None:
    found = exists("/tmp/test.file")
    assert found is False


@pytest.mark.dependency(name="multihash", depends=["write"])
def test_multihash(setup: str) -> None:
    path = os.path.join(setup, "test.file")
    write(path, b"test content")

    assert multihash(path) == TEST_CONTENT_MULTIHASH


def test_multihash_file_not_found(setup: str) -> None:
    with pytest.raises(FileNotFoundError):
        multihash(os.path.join(setup, "does_not_exist.file"))


@pytest.mark.dependency(name="copy_file", depends=["write"])
def test_copy_file(setup: str) -> None:
    source_path = os.path.join(setup, "source.file")
    destination_path = os.path.join(setup, "new_dir/destination.file")
    write(source_path, b"test content")

    copy_file(source_path, destination_path)

    assert read(destination_path) == b"test content"
