from datetime import datetime

from scripts.stac.imagery.generate_metadata import generate_title


def test_generate_imagery_title() -> None:
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    generated_title = generate_title(
        "Rural Aerial Photos", "Auckland", "0.3m", datetime(2023, 1, 1), datetime(2023, 2, 2), "completed"
    )
    assert generated_title == title


def test_generate_dem_title() -> None:
    title = "Auckland LiDAR 0.3m DEM (2023)"
    generated_title = generate_title("DEM", "Auckland", "0.3m", datetime(2023, 1, 1), datetime(2023, 2, 2), "completed")
    assert generated_title == title


def test_generate_dsm_title() -> None:
    title = "Auckland LiDAR 0.3m DSM (2023)"
    generated_title = generate_title("DSM", "Auckland", "0.3m", datetime(2023, 1, 1), datetime(2023, 2, 2), "completed")
    assert generated_title == title


def test_generate_satellite_imagery_title() -> None:
    title = "Auckland 0.5m Satellite Imagery (2023)"
    generated_title = generate_title(
        "Satellite Imagery", "Auckland", "0.5m", datetime(2023, 1, 1), datetime(2023, 2, 2), "completed"
    )
    assert generated_title == title


def test_generate_historic_imagery_title() -> None:
    title = "Auckland 0.3m SNC8844 (2000)"
    generated_title = generate_title(
        "Aerial Photos",
        "Auckland",
        "0.3m",
        datetime(2000, 1, 1),
        datetime(2000, 2, 2),
        "completed",
        historic_survey_number="SNC8844",
    )
    assert generated_title == title


def test_generate_title_long_date() -> None:
    title = "Auckland 0.3m Urban Aerial Photos (2023 - 2024)"
    generated_title = generate_title(
        "Urban Aerial Photos", "Auckland", "0.3m", datetime(2023, 1, 1), datetime(2024, 2, 2), "completed"
    )
    assert generated_title == title


def test_generate_title_location() -> None:
    title = "Banks Penninsula 0.3m Rural Aerial Photos (2023)"
    generated_title = generate_title(
        "Rural Aerial Photos",
        "Canterbury",
        "0.3m",
        datetime(2023, 1, 1),
        datetime(2023, 2, 2),
        "completed",
        location="Banks Penninsula",
    )
    assert generated_title == title


def test_generate_title_event_imagery() -> None:
    title = "Hawke's Bay 0.3m Cyclone Gabrielle Rural Aerial Photos (2023)"
    generated_title = generate_title(
        "Rural Aerial Photos",
        "Hawke's Bay",
        "0.3m",
        datetime(2023, 1, 1),
        datetime(2023, 2, 2),
        "completed",
        event="Cyclone Gabrielle",
    )
    assert generated_title == title


def test_generate_title_event_elevation() -> None:
    title = "Hawke's Bay - Cyclone Gabrielle LiDAR 0.3m DSM (2023)"
    generated_title = generate_title(
        "DSM", "Hawke's Bay", "0.3m", datetime(2023, 1, 1), datetime(2023, 2, 2), "completed", event="Cyclone Gabrielle"
    )
    assert generated_title == title


def test_generate_title_event_satellite_imagery() -> None:
    title = "Hawke's Bay 0.5m Cyclone Gabrielle Satellite Imagery (2023)"
    generated_title = generate_title(
        "Satellite Imagery",
        "Hawke's Bay",
        "0.5m",
        datetime(2023, 1, 1),
        datetime(2023, 2, 2),
        "completed",
        event="Cyclone Gabrielle",
    )
    assert generated_title == title


def test_generate_dsm_title_preview() -> None:
    title = "Auckland LiDAR 0.3m DSM (2023) - preview"
    generated_title = generate_title("DSM", "Auckland", "0.3m", datetime(2023, 1, 1), datetime(2023, 2, 2), "preview")
    assert generated_title == title


def test_generate_imagery_title_empty_optional_str() -> None:
    title = "Auckland 0.3m Rural Aerial Photos (2023)"
    generated_title = generate_title(
        "Rural Aerial Photos",
        "Auckland",
        "0.3m",
        datetime(2023, 1, 1),
        datetime(2023, 2, 2),
        "completed",
        location=None,
        event=None,
    )
    assert generated_title == title
