from datetime import datetime

import pytest
from pytest_subtests import SubTests

from scripts.stac.imagery.collection_context import CollectionContext, MissingMetadataError

# `get_title()` TESTS


def test_get_title_imagery(fake_collection_context: CollectionContext) -> None:
    assert fake_collection_context.title == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_title_dem(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    assert fake_collection_context.title == "Hawke's Bay LiDAR 0.3m DEM (2023)"


def test_get_title_dsm(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "dsm"
    assert fake_collection_context.title == "Hawke's Bay LiDAR 0.3m DSM (2023)"


def test_get_title_satellite_imagery(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "satellite-imagery"
    assert fake_collection_context.title == "Hawke's Bay 0.3m Satellite Imagery (2023)"


def test_get_title_historic_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = "SNC8844"
    assert fake_collection_context.title == "Hawke's Bay 0.3m SNC8844 (2023)"


def test_get_title_historic_imagery_with_missing_number(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = None
    with pytest.raises(MissingMetadataError) as excinfo:
        str(fake_collection_context.title)

    assert "historic_survey_number" in str(excinfo.value)


def test_get_title_long_date(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.end_datetime = datetime(2024, 1, 1)
    assert fake_collection_context.title == "Hawke's Bay 0.3m Rural Aerial Photos (2023-2024)"


def test_get_title_geographic_description(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Ponsonby"
    assert fake_collection_context.title == "Ponsonby 0.3m Rural Aerial Photos (2023)"


def test_get_title_event_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.title == "Hawke's Bay Cyclone Gabrielle 0.3m Rural Aerial Photos (2023)"


def test_get_title_event_elevation(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dsm"
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.title == "Hawke's Bay - Hawke's Bay Cyclone Gabrielle LiDAR 0.3m DSM (2023)"


def test_get_title_event_satellite_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "satellite-imagery"
    fake_collection_context.geographic_description = "Hawke's Bay Cyclone Gabrielle"
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert fake_collection_context.title == "Hawke's Bay Cyclone Gabrielle 0.3m Satellite Imagery (2023)"


def test_get_title_dsm_preview(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dsm"
    fake_collection_context.lifecycle = "preview"
    assert fake_collection_context.title == "Hawke's Bay LiDAR 0.3m DSM (2023) - Preview"


def test_get_title_draft(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.lifecycle = "ongoing"
    assert fake_collection_context.title == "Hawke's Bay 0.3m Rural Aerial Photos (2023) - Draft"


def test_get_title_without_suffix(
    fake_collection_context: CollectionContext,
) -> None:
    """`ongoing` lifecycle nominal case adds a suffix"""
    fake_collection_context.lifecycle = "ongoing"
    fake_collection_context.add_title_suffix = False
    assert fake_collection_context.title == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_get_title_empty_optional_str(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = ""
    fake_collection_context.event_name = ""
    assert fake_collection_context.title == "Hawke's Bay 0.3m Rural Aerial Photos (2023)"


def test_get_title_with_event(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.geographic_description = "Hawke's Bay Forest Assessment"
    fake_collection_context.event_name = "Forest Assessment"
    assert fake_collection_context.title == "Hawke's Bay Forest Assessment 0.3m Rural Aerial Photos (2023)"


# `get_description()` TESTS


def test_get_description_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    assert (
        fake_collection_context.description
        == "Orthophotography within the Hawke's Bay region captured in the 2023 flying season."
    )


def test_get_description_elevation(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    assert fake_collection_context.description == "Digital Elevation Model within the Hawke's Bay region captured in 2023."


def test_get_description_elevation_geographic_description_input(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "dem"
    fake_collection_context.geographic_description = "Central"
    assert fake_collection_context.description == "Digital Elevation Model within the Hawke's Bay region captured in 2023."


def test_get_description_satellite_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "satellite-imagery"
    assert fake_collection_context.description == "Satellite imagery within the Hawke's Bay region captured in 2023."


def test_get_description_historic_imagery(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.category = "scanned-aerial-photos"
    fake_collection_context.historic_survey_number = "SNC8844"
    assert fake_collection_context.description == "Scanned aerial imagery within the Hawke's Bay region captured in 2023."


def test_get_description_event(
    fake_collection_context: CollectionContext,
) -> None:
    fake_collection_context.event_name = "Cyclone Gabrielle"
    assert (
        fake_collection_context.description
        == "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, \
published as a record of the Cyclone Gabrielle event."
    )


# `get_providers()` TESTS


def test_get_providers_default_is_present(fake_collection_context: CollectionContext, subtests: SubTests) -> None:
    # given adding a provider
    fake_collection_context.producers = ["Maxar"]
    providers = fake_collection_context.providers
    with subtests.test(msg="the default provider is still present"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} in providers
    with subtests.test(msg="the new provider is added"):
        assert {"name": "Maxar", "roles": ["producer"]} in providers


def test_get_providers_not_duplicated(fake_collection_context: CollectionContext) -> None:
    fake_collection_context.producers = ["Toitū Te Whenua Land Information New Zealand"]
    fake_collection_context.licensors = ["Toitū Te Whenua Land Information New Zealand"]
    providers = fake_collection_context.providers
    assert len(providers) == 1
    assert providers[0]["name"] == "Toitū Te Whenua Land Information New Zealand"
    assert "host" in providers[0]["roles"]
    assert "processor" in providers[0]["roles"]
    assert "producer" in providers[0]["roles"]
    assert "licensor" in providers[0]["roles"]


def test_get_providers_default_provider_roles_are_kept(fake_collection_context: CollectionContext, subtests: SubTests) -> None:
    # given we are adding a non default role to the default provider
    fake_collection_context.licensors = ["Toitū Te Whenua Land Information New Zealand"]
    fake_collection_context.producers = ["Maxar"]
    providers = fake_collection_context.providers
    with subtests.test(msg="it adds the non default role to the existing default role list"):
        assert {
            "name": "Toitū Te Whenua Land Information New Zealand",
            "roles": ["host", "processor", "licensor"],
        } in providers

    with subtests.test(msg="it does not duplicate the default provider"):
        assert {"name": "Toitū Te Whenua Land Information New Zealand", "roles": ["host", "processor"]} not in providers
