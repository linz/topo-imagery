from scripts.files.file_tiff import FileTiff
from scripts.gdal.tests.gdalinfo import add_band, fake_gdal_info


def test_check_band_count_valid_3() -> None:
    """
    tests check_band_count when the input layer has a valid band count
    which is 3 bands
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo)

    file_tiff = FileTiff("test")
    file_tiff.check_band_count(gdalinfo)

    assert not file_tiff.get_errors()

def test_check_band_count_valid_4() -> None:
    """
    tests check_band_count when the input layer has a valid band count
    which is 4 bands where the fourth band is Alpha
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo, color_interpretation="Alpha")

    file_tiff = FileTiff("test")
    file_tiff.check_band_count(gdalinfo)

    assert not file_tiff.get_errors()


def test_check_band_count_invalid_2() -> None:
    """
    tests check_band_count when the input layer has a invalid band count of 2
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)

    file_tiff = FileTiff("test")
    file_tiff.check_band_count(gdalinfo)

    assert file_tiff.get_errors()

def test_check_band_count_invalid_4() -> None:
    """
    tests check_band_count when the input layer has a invalid 
    band count of 4 wheere the 4th band is not Alpha
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo)
    add_band(gdalinfo)

    file_tiff = FileTiff("test")
    file_tiff.check_band_count(gdalinfo)

    assert file_tiff.get_errors()


def test_check_color_interpretation_valid() -> None:
    """
    tests check_color_interpretation with the correct color interpretation
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")

    file_tiff = FileTiff("test")
    file_tiff.check_color_interpretation(gdalinfo)

    assert not file_tiff.get_errors()


def test_check_color_interpretation_invalid() -> None:
    """
    tests check_color_interpretation with the incorrect color interpretation
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")
    add_band(gdalinfo, color_interpretation="undefined")

    file_tiff = FileTiff("test")
    file_tiff.check_color_interpretation(gdalinfo)

    assert file_tiff.get_errors()


def test_check_no_data_valid() -> None:
    """
    tests check_no_data when the input layer has a valid no data value of 255
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, no_data_value=255)

    file_tiff = FileTiff("test")
    file_tiff.check_no_data(gdalinfo)

    assert not file_tiff.get_errors()


def test_check_no_data_valid_alpha() -> None:
    """
    tests check_no_data when the input layer has no no_data value assigned and Alpha
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="red")
    add_band(gdalinfo, color_interpretation="green")
    add_band(gdalinfo, color_interpretation="blue")
    add_band(gdalinfo, color_interpretation="Alpha")

    file_tiff = FileTiff("test")
    file_tiff.check_no_data(gdalinfo)

    assert not file_tiff.get_errors()


def test_check_no_data_invalid_not_alpha() -> None:
    """
    tests check_no_data when the input layer has no no_data value assigned and invalid fourth band
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="red")
    add_band(gdalinfo, color_interpretation="green")
    add_band(gdalinfo, color_interpretation="blue")
    add_band(gdalinfo, color_interpretation="invalid")

    file_tiff = FileTiff("test")
    file_tiff.check_no_data(gdalinfo)

    assert file_tiff.get_errors()


def test_check_no_data_no_value() -> None:
    """
    tests check_no_data when the input layer has no no_data value assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)

    file_tiff = FileTiff("test")
    file_tiff.check_no_data(gdalinfo)

    assert file_tiff.get_errors()

def test_is_no_data_true() -> None:
    """
    tests is_no_data when the input layer that has no_data value assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, no_data_value=255)

    file_tiff = FileTiff("test")
    assert file_tiff.is_no_data(gdalinfo)

def test_is_no_data_false() -> None:
    """
    tests is_no_data when the input layer that does not have no_data value assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo)

    file_tiff = FileTiff("test")
    assert not file_tiff.is_no_data(gdalinfo)


def test_check_no_data_invalid_value() -> None:
    """
    tests check_no_data when the input layer has the wrong value of 0 assigned
    """
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, no_data_value=0)

    file_tiff = FileTiff("test")
    file_tiff.check_no_data(gdalinfo)

    assert file_tiff.get_errors()


def test_check_srs_valid() -> None:
    """
    tests check_srs with the same srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Test"

    file_tiff = FileTiff("test")
    file_tiff.set_srs(srs_to_test_against)
    file_tiff.check_srs(srs_tif)

    assert not file_tiff.get_errors()


def test_check_srs_invalid() -> None:
    """
    tests check_srs with a different srs value
    """
    srs_to_test_against = b"SRS Test"
    srs_tif = b"SRS Different"

    file_tiff = FileTiff("test")
    file_tiff.set_srs(srs_to_test_against)
    file_tiff.check_srs(srs_tif)

    assert file_tiff.get_errors()
