from typing import Optional, cast

from scripts.files.file_check import FileCheck
from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand


def fake_gdal_info() -> GdalInfo:
    return cast(GdalInfo, {})


def add_band(gdalinfo: GdalInfo, color_interpretation: Optional[str] = None, no_data_value: Optional[int] = None) -> None:
    if gdalinfo.get("bands", None) is None:
        gdalinfo["bands"] = []

    gdalinfo["bands"].append(
        cast(
            GdalInfoBand,
            {"band": len(gdalinfo["bands"]), "colorInterpretation": color_interpretation, "noDataValue": no_data_value},
        )
    )


def test_check_band_count_valid() -> None:
    """
    tests check_band_count when the input layer has a valid band count
    which is 3 bands
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo)

    file_check = FileCheck("test", 500, b"test")
    file_check.check_band_count(gdalinfo)

    assert not file_check.errors


def test_check_band_count_invalid() -> None:
    """
    tests check_band_count when the input layer has a invalid band count of 2
    which is 3 bands to be valid
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)

    file_check = FileCheck("test", 500, b"test")
    file_check.check_band_count(gdalinfo)

    assert file_check.errors


def test_check_color_interpretation_valid() -> None:
    """
    tests check_color_interpretation with the correct color interpretation
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")

    file_check = FileCheck("test", 500, b"test")
    file_check.check_color_interpretation(gdalinfo)

    assert not file_check.errors


def test_check_color_interpretation_invalid() -> None:
    """
    tests check_color_interpretation with the incorrect color interpretation
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")
    add_band(gdalinfo, color_interpretation="undefined")

    file_check = FileCheck("test", 500, b"test")
    file_check.check_color_interpretation(gdalinfo)

    assert file_check.errors


def test_check_no_data_valid() -> None:
    """
    tests check_no_data when the input layer has a valid no data value of 255
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, no_data_value=255)

    file_check = FileCheck("test", 500, b"test")
    file_check.check_no_data(gdalinfo)

    assert not file_check.errors


def test_check_no_data_no_value() -> None:
    """
    tests check_no_data when the input layer has no no_data value assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)

    file_check = FileCheck("test", 500, b"test")
    file_check.check_no_data(gdalinfo)

    assert file_check.errors


def test_check_no_data_invalid_value() -> None:
    """
    tests check_no_data when the input layer has the wrong value of 0 assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, no_data_value=0)

    file_check = FileCheck("test", 500, b"test")
    file_check.check_no_data(gdalinfo)

    assert file_check.errors


def test_check_srs_valid() -> None:
    """
    tests check_srs with the same srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Test"

    file_check = FileCheck("test", 500, srs_to_test_against)
    file_check.check_srs(srs_tif)

    assert not file_check.errors


def test_check_srs_invalid() -> None:
    """
    tests check_srs with a different srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Different"

    file_check = FileCheck("test", 500, srs_to_test_against)
    file_check.check_srs(srs_tif)

    assert file_check.errors
