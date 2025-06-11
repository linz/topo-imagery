from decimal import Decimal
from random import choice, randint
from string import ascii_lowercase
from typing import Iterator

import pytest

from scripts.stac.imagery.collection_context import CollectionContext


def fake_linz_slug() -> str:
    random_string = "".join(choice(ascii_lowercase) for _ in range(6))
    start_year = randint(2000, 2009)
    end_year = randint(2010, 2019)
    gsd = choice([0.75, 0.3, 1, 0.075])

    return f"a-random-slug-{random_string}_{start_year}-{end_year}_{gsd}m"


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
