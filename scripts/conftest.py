from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import choice, randint
from string import ascii_lowercase
from typing import Iterator

import pytest

from scripts.datetimes import format_rfc_3339_datetime_string
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


def any_epoch_datetime() -> datetime:
    """
    Get arbitrary datetime
    """
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    return any_datetime_between(start, end)


def any_datetime_between(start: datetime, end: datetime) -> datetime:
    """
    Get arbitrary datetime between start (inclusive) and end (exclusive), with second precision.
    """
    range_in_seconds = (end - start).total_seconds()
    return start + timedelta(seconds=randint(0, int(range_in_seconds)))


def any_epoch_datetime_string() -> str:
    return format_rfc_3339_datetime_string(any_epoch_datetime())
