from pytest import raises

from scripts.gdal.gdal_bands import get_gdal_band_offset, get_gdal_band_type
from scripts.gdal.gdal_presets import CompressionPreset
from scripts.gdal.tests.gdalinfo import add_band, add_palette_band, fake_gdal_info


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


def test_gdal_grey_bands_dem_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Gray")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo, CompressionPreset.DEM_LERC.value)

    assert " ".join(bands) == "-b 1"


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


def test_gdal_rgba_palette_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_palette_band(gdalinfo, colour_table_entries=[[x, x, x, 255] for x in reversed(range(256))])

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-expand rgba"


def test_gdal_rgb_palette_detection() -> None:
    gdalinfo = fake_gdal_info()
    add_palette_band(gdalinfo, colour_table_entries=[[x, x, x] for x in reversed(range(256))])

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-expand rgb"


# Older greyscale historical scanned imagery was standardised as 4 band GGGA from paletted source TIFFs
def test_gdal_ggga() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Gray")
    add_band(gdalinfo, color_interpretation="Gray")
    add_band(gdalinfo, color_interpretation="Gray")
    add_band(gdalinfo, color_interpretation="Alpha")

    bands = get_gdal_band_offset("some_file.tiff", gdalinfo)

    assert " ".join(bands) == "-b 1 -b 1 -b 1 -b 4"


def test_gdal_default_rg_missing_b() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, color_interpretation="Red")
    add_band(gdalinfo, color_interpretation="Green")

    with raises(RuntimeError):
        get_gdal_band_offset("some_file.tiff", gdalinfo)


def test_get_band_type() -> None:
    gdalinfo = fake_gdal_info()
    add_band(gdalinfo, band_type="UInt16")
    add_band(gdalinfo, band_type="UInt16")
    add_band(gdalinfo, band_type="UInt16")

    band_type = get_gdal_band_type("some_file.tiff", gdalinfo)

    assert band_type == "UInt16"
