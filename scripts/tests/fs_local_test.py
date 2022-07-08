from shutil import rmtree
from tempfile import mkdtemp
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def setup() -> Generator[str, None, None]:
    """
    This function creates a temporary directory and deletes it after each test.
    See following link for details:
    https://docs.pytest.org/en/stable/fixture.html#yield-fixtures-recommended
    """
    target = mkdtemp()
    yield target
    rmtree(target)


def test_read(setup) -> None:
    pass
