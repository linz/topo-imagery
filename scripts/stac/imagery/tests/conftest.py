from datetime import datetime
from typing import Generator

import pytest

from scripts.stac.imagery.metadata_constants import CollectionMetadata


@pytest.fixture(autouse=True)
def fake_collection_metadata() -> Generator[CollectionMetadata, None, None]:
    collection_metadata: CollectionMetadata = {
        "category": "rural-aerial-photos",
        "region": "hawkes-bay",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "event_name": None,
        "historic_survey_number": None,
        "geographic_description": None,
    }
    yield collection_metadata
