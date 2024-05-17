import os
from pathlib import Path

import pytest

from scripts.files.fs_local import exists, modified, read, write
from scripts.tests.datetimes_test import any_epoch_datetime


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


def test_should_get_modified_datetime(setup: str) -> None:
    path = Path(os.path.join(setup, "modified.file"))
    path.touch()
    modified_datetime = any_epoch_datetime()
    os.utime(path, times=(any_epoch_datetime().timestamp(), modified_datetime.timestamp()))
    assert modified(path) == modified_datetime
