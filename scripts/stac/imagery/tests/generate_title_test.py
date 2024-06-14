from datetime import datetime
from typing import Generator

import pytest

from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionMetadata, MissingMetadataError
from scripts.tests.datetimes_test import any_epoch_datetime


# pylint: disable=duplicate-code
@pytest.fixture(name="metadata", autouse=True)
def setup() -> Generator[tuple[CollectionMetadata, CollectionMetadata], None, None]:
    metadata_auck: CollectionMetadata = {
        "category": "rural-aerial-photos",
        "region": "auckland",
        "gsd": "0.3m",
        "start_datetime": datetime(2023, 1, 1),
        "end_datetime": datetime(2023, 2, 2),
        "lifecycle": "completed",
        "event_name": None,
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
        "event_name": None,
        "historic_survey_number": None,
        "geographic_description": None,
    }
    yield (metadata_auck, metadata_hb)


def test_generate_imagery_title(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    assert collection.stac["title"] == title


def test_generate_dem_title(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dem"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland LiDAR 0.3m DEM (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dsm"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_satellite_imagery_title(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "satellite-imagery"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    title = "Auckland 0.3m SNC8844 (2023)"
    metadata_auck, _ = metadata
    metadata_auck["category"] = "scanned-aerial-photos"
    metadata_auck["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title_missing_number(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "scanned-aerial-photos"
    metadata_auck["historic_survey_number"] = None
    with pytest.raises(MissingMetadataError) as excinfo:
        ImageryCollection(metadata_auck, any_epoch_datetime)

    assert "historic_survey_number" in str(excinfo.value)


def test_generate_title_long_date(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["end_datetime"] = datetime(2024, 1, 1)
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland 0.3m Rural Aerial Photos (2023-2024)"
    assert collection.stac["title"] == title


def test_generate_title_geographic_description(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["geographic_description"] = "Ponsonby"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Ponsonby 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_imagery(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb, any_epoch_datetime)
    title = "Hawke's Bay Cyclone Gabrielle 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_elevation(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "dsm"
    metadata_hb["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb, any_epoch_datetime)
    title = "Hawke's Bay - Hawke's Bay Cyclone Gabrielle LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_satellite_imagery(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["category"] = "satellite-imagery"
    metadata_hb["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    metadata_hb["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(metadata_hb, any_epoch_datetime)
    title = "Hawke's Bay Cyclone Gabrielle 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title_preview(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["category"] = "dsm"
    metadata_auck["lifecycle"] = "preview"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland LiDAR 0.3m DSM (2023) - Preview"
    assert collection.stac["title"] == title


def test_generate_imagery_title_draft(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    _, metadata_hb = metadata
    metadata_hb["lifecycle"] = "ongoing"
    collection = ImageryCollection(metadata_hb, any_epoch_datetime)
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023) - Draft"
    assert collection.stac["title"] == title


def test_generate_imagery_title_empty_optional_str(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["geographic_description"] = ""
    metadata_auck["event_name"] = ""
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_imagery_title_with_event(metadata: tuple[CollectionMetadata, CollectionMetadata]) -> None:
    metadata_auck, _ = metadata
    metadata_auck["geographic_description"] = "Auckland Forest Assessment"
    metadata_auck["event_name"] = "Forest Assessment"
    collection = ImageryCollection(metadata_auck, any_epoch_datetime)
    title = "Auckland Forest Assessment 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title
