import os
from shutil import rmtree
from tempfile import mkdtemp
from typing import Generator

import pytest

from scripts.files.fs_local import read, rename, write


@pytest.fixture(name="setup", autouse=True)
def fixture_setup() -> Generator[str, None, None]:
    """
    This function creates a temporary directory and deletes it after each test.
    See following link for details:
    https://docs.pytest.org/en/stable/fixture.html#yield-fixtures-recommended
    """
    target = mkdtemp()
    yield target
    rmtree(target)


@pytest.mark.dependency(name="write")
def test_write(setup: str) -> None:
    target = setup
    path = os.path.join(target, "test.file")
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


@pytest.mark.dependency(name="rename", depends=["write"])
def test_rename(setup: str) -> None:
    content = b"content"
    target = setup
    path = os.path.join(target, "testA.file")
    write(path, content)
    new_path = os.path.join(target, "testB.file")
    rename(path, new_path)
    assert os.path.exists(new_path)
    assert not os.path.exists(path)
