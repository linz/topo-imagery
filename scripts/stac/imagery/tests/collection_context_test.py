from datetime import datetime

import pytest

from scripts.stac.imagery.collection_context import CollectionContext, MissingMetadataError

# `get_title()` TESTS


def test_get_title_imagery(fake_collection_context: CollectionContext) -> None:
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_title_dem(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    assert fake_collection_context.get_title() == "Hawke's Bay LiDAR 0.3m DEM (2023)"


def test_get_title_dsm(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "dsm"
    assert fake_collection_context.get_title() == "Hawke's Bay LiDAR 0.3m DSM (2023)"


def test_get_title_satellite_imagery(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "satellite-imagery"
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Satellite Imagery (2023)"


def test_get_title_historic_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = "SNC8844"
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m SNC8844 (2023)"


def test_get_title_historic_imagery_with_missing_number(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = None
    with pytest.raises(MissingMetadataError) as excinfo:
        fake_collection_context.get_title()

    assert "historic_survey_number" in str(excinfo.value)


def test_get_title_long_date(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.end_datetime = datetime(2024, 1, 1)
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Rural Aerial Photos (2023-2024)"


def test_get_title_geographic_description(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Ponsonby"
    assert fake_collection_context.get_title() == "Ponsonby 0.3m Rural Aerial Photos (2023)"


def test_get_title_event_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.get_title() == "Hawke's Bay Cyclone Gabrielle 0.3m Rural Aerial Photos (2023)"


def test_get_title_event_elevation(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dsm"
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.get_title() == "Hawke's Bay - Hawke's Bay Cyclone Gabrielle LiDAR 0.3m DSM (2023)"


def test_get_title_event_satellite_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "satellite-imagery"
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.get_title() == "Hawke's Bay Cyclone Gabrielle 0.3m Satellite Imagery (2023)"


def test_get_title_dsm_preview(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dsm"
    fake_collection_context.lifecycle = "preview"
    assert fake_collection_context.get_title() == "Hawke's Bay LiDAR 0.3m DSM (2023) - Preview"


def test_get_title_draft(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.lifecycle = "ongoing"
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Rural Aerial Photos (2023) - Draft"


def test_get_title_without_suffix(
    fake_collection_context: CollectionContext,
) -> None:
    """`ongoing` lifecycle nominal case adds a suffix"""
    fake_collection_context.lifecycle = "ongoing"
    fake_collection_context.add_title_suffix = False
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_get_title_empty_optional_str(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = ""
    fake_collection_context.event_name = ""
    assert fake_collection_context.get_title() == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_get_title_with_event(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Hawke's Bay Forest Assessment"
    fake_collection_context.event_name = "Forest Assessment"
    assert fake_collection_context.get_title() == "Hawke's Bay Forest Assessment 0.3m Rural Aerial Photos (2023)"


# `get_description()` TESTS


def test_get_description_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    assert (
        fake_collection_context.get_description()
        == "Orthophotography within the Hawke's Bay region captured in the 2023 flying season."
    )


def test_get_description_elevation(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    assert (
        fake_collection_context.get_description() == "Digital Elevation Model within the Hawke's Bay region captured in 2023."
    )


def test_get_description_elevation_geographic_description_input(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    fake_collection_context.geographic_description = "Central"
    assert (
        fake_collection_context.get_description() == "Digital Elevation Model within the Hawke's Bay region captured in 2023."
    )


def test_get_description_satellite_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "satellite-imagery"
    assert fake_collection_context.get_description() == "Satellite imagery within the Hawke's Bay region captured in 2023."


def test_get_description_historic_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = "SNC8844"
    assert (
        fake_collection_context.get_description() == "Scanned aerial imagery within the Hawke's Bay region captured in 2023."
    )


def test_get_description_event(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert (
        fake_collection_context.get_description()
        == "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, \
published as a record of the Cyclone Gabrielle event."
    )
