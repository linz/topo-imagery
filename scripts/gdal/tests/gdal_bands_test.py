from scripts.gdal.gdal_bands import get_gdal_band_offset, get_gdal_band_type
from scripts.gdal.tests.gdalinfo import add_band, fake_gdal_info


def test_gdal_grey_bands() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Gray")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 1 -b 1 -b 1"


def test_gdal_grey_bands_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Alpha")
    add_band(gdalinfo, color_interpretation="Gray")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 2 -b 2 -b 2 -b 1"


def test_gdal_rgba_bands_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Alpha")
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 2 -b 3 -b 4 -b 1"


def test_gdal_rgb_bands_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")
    add_band(gdalinfo, color_interpretation="Blue")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 1 -b 2 -b 3"


def test_gdal_default_grey_scale() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Pallette")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 1 -b 1 -b 1"


def test_gdal_default_rgb() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="R")
    add_band(gdalinfo, color_interpretation="G")
    add_band(gdalinfo, color_interpretation="B")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 1 -b 2 -b 3"


def test_get_band_type() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, band_type="UInt16")
    add_band(gdalinfo, band_type="UInt16")
    add_band(gdalinfo, band_type="UInt16")

    band_type = get_gdal_band_type("some_file.tiff", gdalinfo)

    assert band_type == "UInt16"
