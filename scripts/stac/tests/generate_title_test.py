from datetime import datetime
from typing import Generator, Tuple

import pytest

from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionTitleMetadata


@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[Tuple[CollectionTitleMetadata, CollectionTitleMetadata], None, None]:
    metadata_auck: CollectionTitleMetadata = {
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
    metadata_hb: CollectionTitleMetadata = {
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


def test_generate_imagery_title(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    collection = ImageryCollection(metadata_auck)
    assert collection.stac["title"] == title


def test_generate_dem_title(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "DEM"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DEM (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "DSM"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_satellite_imagery_title(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "Satellite Imagery"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    title = "Auckland 0.3m SNC8844 (2023)"
    metadata_auck, _ = metadata
    metadata_auck["category"] = "Aerial Photos"
    metadata_auck["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(metadata_auck)
    assert collection.stac["title"] == title


def test_generate_title_long_date(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["end_datetime"] = datetime(2024, 1, 1)
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Rural Aerial Photos (2023-2024)"
    assert collection.stac["title"] == title


def test_generate_title_location(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["location"] = "Ponsonby"
    collection = ImageryCollection(metadata_auck)
    title = "Ponsonby 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_imagery(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["event"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay 0.3m Cyclone Gabrielle Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_elevation(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "DSM"
    metadata_hb["event"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay - Cyclone Gabrielle LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_satellite_imagery(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "Satellite Imagery"
    metadata_hb["event"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb)
    title = "Hawke's Bay 0.3m Cyclone Gabrielle Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title_preview(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "DSM"
    metadata_auck["lifecycle"] = "preview"
    collection = ImageryCollection(metadata_auck)
    title = "Auckland LiDAR 0.3m DSM (2023) - Preview"
    assert collection.stac["title"] == title


def test_generate_imagery_title_empty_optional_str(metadata: Tuple[CollectionTitleMetadata, CollectionTitleMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["location"] = ""
    metadata_auck["event"] = ""
    collection = ImageryCollection(metadata_auck)
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title
