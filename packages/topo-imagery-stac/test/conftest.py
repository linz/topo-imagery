from decimal import Decimal
from typing import Iterator

import pytest

from test_helpers import fake_linz_slug
from topo_imagery_stac.imagery.collection_context import CollectionContext


@pytest.fixture
def fake_collection_context() -> Iterator[CollectionContext]:
    yield CollectionContext(
        category="rural-aerial-photos",
        domain="land",
        region="hawkes-bay",
        gsd=Decimal("0.3"),
        lifecycle="completed",
        linz_slug=fake_linz_slug(),
        collection_id="a-random-collection-id",
    )
