from datetime import datetime
from decimal import Decimal
from typing import Iterator

import pytest

from scripts.stac.imagery.metadata_constants import CollectionMetadata


@pytest.fixture
def fake_collection_metadata() -> Iterator[CollectionMetadata]:
    collection_metadata: CollectionMetadata = {
        "category": "rural-aerial-photos",
        "region": "hawkes-bay",
        "gsd": Decimal("0.3"),
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "event_name": None,
        "historic_survey_number": None,
        "geographic_description": None,
    }
    yield collection_metadata


@pytest.fixture
def fake_linz_slug() -> str:
    return "somewhere-in-new-zealand_2021-2023_0.75m"
