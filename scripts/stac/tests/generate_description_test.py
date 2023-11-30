from datetime import datetime

from scripts.stac.imagery.generate_metadata import generate_description


def test_generate_description_imagery() -> None:
    description = "Orthophotography within the Auckland region captured in the 2023 flying season."
    generated_description = generate_description("Rural Aerial Photos", "Auckland", datetime(2023, 1, 1), datetime(2023, 2, 2))
    assert generated_description == description


def test_generate_description_elevation() -> None:
    description = "Digital Elevation Model within the Auckland region in 2023."
    generated_description = generate_description("DEM", "Auckland", datetime(2023, 1, 1), datetime(2023, 2, 2))
    assert generated_description == description


def test_generate_description_elevation_location_input() -> None:
    description = "Digital Elevation Model within the Auckland - Central region in 2023."
    generated_description = generate_description(
        "DEM", "Auckland", datetime(2023, 1, 1), datetime(2023, 2, 2), location="Central"
    )
    assert generated_description == description


def test_generate_description_satellite_imagery() -> None:
    description = "Satellite imagery within the Auckland region captured in 2023."
    generated_description = generate_description("Satellite Imagery", "Auckland", datetime(2023, 1, 1), datetime(2023, 2, 2))
    assert generated_description == description


def test_generate_description_historic_imagery() -> None:
    description = "Scanned aerial imagery within the Auckland region captured in 2000."
    generated_description = generate_description(
        "Aerial Photos", "Auckland", datetime(2000, 1, 1), datetime(2000, 2, 2), historic_survey_number="SNC8844"
    )
    assert generated_description == description


def test_generate_description_event() -> None:
    description = "Orthophotography within the Hawke's Bay region captured in the 2023 flying season, \
        published as a record of the Cyclone Gabrielle event."
    generated_description = generate_description(
        "Rural Aerial Photos", "Hawke's Bay", datetime(2023, 1, 1), datetime(2023, 2, 2), event="Cyclone Gabrielle"
    )
    assert generated_description == description
