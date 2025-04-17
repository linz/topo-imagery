from datetime import datetime

import pytest
from pytest_subtests import SubTests

from scripts.stac.imagery.collection_context import CollectionContext, MissingMetadataError

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
