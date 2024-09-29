from scripts.stac.imagery.collection import ImageryCollection
from scripts.stac.imagery.metadata_constants import CollectionMetadata
from scripts.tests.datetimes_test import any_epoch_datetime


def test_generate_description_imagery(fake_collection_metadata: CollectionMetadata) -> None:
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Orthophotography within the Hawke's Bay region captured in the 2023 flying season."
    assert collection.stac["description"] == description


def test_generate_description_elevation(fake_collection_metadata: CollectionMetadata) -> None:
    fake_collection_metadata["category"] = "dem"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Digital Elevation Model within the Hawke's Bay region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_elevation_geographic_description_input(fake_collection_metadata: CollectionMetadata) -> None:
    fake_collection_metadata["category"] = "dem"
    fake_collection_metadata["geographic_description"] = "Central"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Digital Elevation Model within the Hawke's Bay region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_satellite_imagery(fake_collection_metadata: CollectionMetadata) -> None:
    fake_collection_metadata["category"] = "satellite-imagery"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Satellite imagery within the Hawke's Bay region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_historic_imagery(fake_collection_metadata: CollectionMetadata) -> None:
    fake_collection_metadata["category"] = "scanned-aerial-photos"
    fake_collection_metadata["historic_survey_number"] = "SNC8844"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Scanned aerial imagery within the Hawke's Bay region captured in 2023."
    assert collection.stac["description"] == description


def test_generate_description_event(fake_collection_metadata: CollectionMetadata) -> None:
    fake_collection_metadata["event_name"] = "Cyclone Gabrielle"
    collection = ImageryCollection(fake_collection_metadata, any_epoch_datetime)
    description = "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, \
published as a record of the Cyclone Gabrielle event."
    assert collection.stac["description"] == description
