from typing import Iterator

import pytest
from topo_imagery_stac.imagery.collection_context import CollectionContext
from topo_imagery_stac.testing.helpers import any_collection_context


@pytest.fixture
def fake_collection_context() -> Iterator[CollectionContext]:
    yield any_collection_context()
