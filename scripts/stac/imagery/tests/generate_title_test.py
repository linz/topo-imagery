from datetime import datetime

import pytest

from scripts.stac.imagery.collection import CollectionIdentifiers, ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionMetadata, MissingMetadataError
from scripts.tests.datetimes_test import any_epoch_datetime_string


def test_generate_imagery_title(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023)"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    assert collection.stac["title"] == title


def test_generate_dem_title(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "dem"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay LiDAR 0.3m DEM (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "dsm"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_satellite_imagery_title(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "satellite-imagery"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    title = "Hawke's Bay 0.3m SNC8844 (2023)"
    fake_collection_metadata["category"] = "scanned-aerial-photos"
    fake_collection_metadata["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    assert collection.stac["title"] == title


def test_generate_historic_imagery_title_missing_number(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "scanned-aerial-photos"
    fake_collection_metadata["historic_survey_number"] = None
    with pytest.raises(MissingMetadataError) as excinfo:
        ImageryCollection(
            fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
        )

    assert "historic_survey_number" in str(excinfo.value)


def test_generate_title_long_date(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["end_datetime"] = datetime(2024, 1, 1)
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023-2024)"
    assert collection.stac["title"] == title


def test_generate_title_geographic_description(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["geographic_description"] = "Ponsonby"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Ponsonby 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_imagery(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_metadata["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay Cyclone Gabrielle 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_elevation(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "dsm"
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_metadata["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay - Hawke's Bay Cyclone Gabrielle LiDAR 0.3m DSM (2023)"
    assert collection.stac["title"] == title


def test_generate_title_event_satellite_imagery(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "satellite-imagery"
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_metadata["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay Cyclone Gabrielle 0.3m Satellite Imagery (2023)"
    assert collection.stac["title"] == title


def test_generate_dsm_title_preview(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["category"] = "dsm"
    fake_collection_metadata["lifecycle"] = "preview"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay LiDAR 0.3m DSM (2023) - Preview"
    assert collection.stac["title"] == title


def test_generate_imagery_title_draft(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["lifecycle"] = "ongoing"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023) - Draft"
    assert collection.stac["title"] == title


def test_generate_imagery_title_without_suffix(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    # `ongoing` lifecycle nominal case adds a suffix
    fake_collection_metadata["lifecycle"] = "ongoing"
    collection = ImageryCollection(
        metadata=fake_collection_metadata,
        created_datetime=any_epoch_datetime_string(),
        updated_datetime=any_epoch_datetime_string(),
        identifiers=fake_collection_identifiers,
        add_title_suffix=False,
    )
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_imagery_title_empty_optional_str(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["geographic_description"] = ""
    fake_collection_metadata["event_name"] = ""
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title


def test_generate_imagery_title_with_event(
    fake_collection_metadata: CollectionMetadata, fake_collection_identifiers: CollectionIdentifiers
) -> None:
    fake_collection_metadata["geographic_description"] = "Hawke's Bay Forest Assessment"
    fake_collection_metadata["event_name"] = "Forest Assessment"
    collection = ImageryCollection(
        fake_collection_metadata, any_epoch_datetime_string(), any_epoch_datetime_string(), fake_collection_identifiers
    )
    title = "Hawke's Bay Forest Assessment 0.3m Rural Aerial Photos (2023)"
    assert collection.stac["title"] == title
