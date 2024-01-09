from datetime import datetime
from typing import Generator, Tuple

import pytest

from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionMetadata


@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[Tuple[CollectionMetadata, CollectionMetadata], None, None]:
    metadata_auck: CollectionMetadata = {
        "category": "rural-aerial-photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "location": None,
        "event_name": "Forest assessment",
        "historic_survey_number": None,
        "geographic_description": None,
    }
    metadata_hb: CollectionMetadata = {
        "category": "rural-aerial-photos",
        "region": "hawkes-bay",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "location": None,
        "event_name": "Forest assessment",
        "historic_survey_number": None,
        "geographic_description": None,
    }
    yield (metadata_auck, metadata_hb)


def test_generate_imagery_title(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    collection = ImageryCollection(metadata_auck)
    assert collection.stac["title"] == title


def test_generate_dem_title(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dem"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DEM (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dsm"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_satellite_imagery_title(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "satellite-imagery"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    title = "Auckland 0.3m SNC8844 (2023)"
    metadata_auck, _ = metadata
    metadata_auck["category"] = "aerial-photos"
    metadata_auck["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(metadata_auck)
    assert collection.stac["title"] == title


def test_generate_title_long_date(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["end_datetime"] = datetime(2024, 1, 1)
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Rural Aerial Photos (2023-2024)"
    assert collection.stac["title"] == title


def test_generate_title_location(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["location"] = "Ponsonby"
    collection = ImageryCollection(metadata_auck)
    title = "Ponsonby 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_imagery(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay 0.3m Cyclone Gabrielle Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_elevation(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "dsm"
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay - Cyclone Gabrielle LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_satellite_imagery(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "satellite-imagery"
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay 0.3m Cyclone Gabrielle Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title_preview(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dsm"
    metadata_auck["lifecycle"] = "preview"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DSM (2023) - Preview"
    assert collection.stac["title"] == title


def test_generate_imagery_title_empty_optional_str(metadata: Tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["location"] = ""
    metadata_auck["event_name"] = ""
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title
