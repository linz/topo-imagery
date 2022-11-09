from typing import Generator

import pytest

from scripts.stac.imagery.collection import ImageryCollection


@pytest.fixture(autouse=True)
def setup() -> Generator[ImageryCollection, None, None]:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)
    yield collection
