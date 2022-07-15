from typing import Dict

from non_visual_qa import check_band_count, check_color_interpretation, check_no_data, check_srs


def test_check_band_count_valid() -> None:
    """
    tests check_band_count when the input layer has a valid band count
    which is 3 bands
    """
    gdalinfo = {}
    gdalinfo["bands"] = [{"band": 1}, {"band": 2}, {"band": 3}]
    errors: Dict[str, str] = {}

    check_band_count(gdalinfo, errors)
    assert not errors


def test_check_band_count_invalid() -> None:
    """
    tests check_band_count when the input layer has a invalid band count of 2
    which is 3 bands to be valid
    """
    gdalinfo = {}
    gdalinfo["bands"] = [{"band": 1}, {"band": 2}]
    errors: Dict[str, str] = {}

    check_band_count(gdalinfo, errors)
    assert errors


def test_check_color_interpretation_valid() -> None:
    """
    tests check_color_interpretation with the correct color interpretation
    """
    gdalinfo = {}
    gdalinfo["bands"] = [
        {
            "colorInterpretation": "Red",
        },
        {
            "colorInterpretation": "Green",
        },
        {
            "colorInterpretation": "Blue",
        },
    ]
    errors: Dict[str, str] = {}

    check_color_interpretation(gdalinfo, errors)
    assert not errors


def test_check_color_interpretation_invalid() -> None:
    """
    tests check_color_interpretation with the incorrect color interpretation
    """
    gdalinfo = {}
    gdalinfo["bands"] = [
        {
            "colorInterpretation": "Red",
        },
        {
            "colorInterpretation": "Green",
        },
        {
            "colorInterpretation": "Blue",
        },
        {
            "colorInterpretation": "Undefined",
        },
    ]
    errors: Dict[str, str] = {}

    check_color_interpretation(gdalinfo, errors)
    assert errors


def test_check_no_data_valid() -> None:
    """
    tests check_no_data when the input layer has a valid no data value of 255
    """
    gdalinfo = {}
    gdalinfo["bands"] = [
        {
            "noDataValue": 255,
        }
    ]
    errors: Dict[str, str] = {}

    check_no_data(gdalinfo, errors)
    assert not errors


def test_check_no_data_no_value() -> None:
    """
    tests check_no_data when the input layer has no no_data value assigned
    """
    gdalinfo = {}
    gdalinfo["bands"] = [{"test": 1}]
    errors: Dict[str, str] = {}

    check_no_data(gdalinfo, errors)
    assert errors


def test_check_no_data_invalid_value() -> None:
    """
    tests check_no_data when the input layer has the wrong value of 0 assigned
    """
    gdalinfo = {}
    gdalinfo["bands"] = [
        {
            "noDataValue": 0,
        }
    ]
    errors: Dict[str, str] = {}

    check_no_data(gdalinfo, errors)
    assert errors


def test_check_srs_valid() -> None:
    """
    tests check_srs with the same srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Test"
    errors: Dict[str, str] = {}

    check_srs(srs_to_test_against, srs_tif, errors)
    assert not errors


def test_check_srs_invalid() -> None:
    """
    tests check_srs with a different srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Different"
    errors: Dict[str, str] = {}

    check_srs(srs_to_test_against, srs_tif, errors)
    assert errors
