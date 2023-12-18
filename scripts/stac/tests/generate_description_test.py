from datetime import datetime
from typing import Generator, Tuple

import pytest

from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionMetadata


@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[Tuple[CollectionMetadata, CollectionMetadata], None, None]:
    metadata_auck: CollectionMetadata = {
        "category": "Rural Aerial Photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "location": None,
        "event": None,
        "historic_survey_number": None,
    }
    metadata_hb: CollectionMetadata = {
        "category": "Rural Aerial Photos",
        "region": "hawkes-bay",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "location": None,
        "event": None,
        "historic_survey_number": None,
    }
    yield (metadata_auck, metadata_hb)


def test_generate_description_imagery(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    collection = ImageryCollection(metadata_auck)
    description = "Orthophotography within the Auckland region captured in the 2023 flying season."
    assert collection.stac["description"] == description


def test_generate_description_elevation(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "DEM"
    collection = ImageryCollection(metadata_auck)
    description = "Digital Elevation Model within the Auckland region in 2023."
    assert collection.stac["description"] == description


def test_generate_description_elevation_location_input(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "DEM"
    metadata_auck["location"] = "Central"
    collection = ImageryCollection(metadata_auck)
    description = "Digital Elevation Model within the Auckland - Central region in 2023."
    assert collection.stac["description"] == description


def test_generate_description_satellite_imagery(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "Satellite Imagery"
    collection = ImageryCollection(metadata_auck)
    description = "Satellite imagery within the Auckland region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_historic_imagery(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "Aerial Photos"
    metadata_auck["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(metadata_auck)
    description = "Scanned aerial imagery within the Auckland region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_event(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["event"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    description = "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, \
published as a record of the Cyclone Gabrielle event."
    assert collection.stac["description"] == description
