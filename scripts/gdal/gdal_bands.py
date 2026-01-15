from linz_logger import get_log

from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdal_presets import CompressionPreset
from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand


def find_band(bands: list[GdalInfoBand], color: str) -> GdalInfoBand | None:
    """Look for a specific colorInterpretation inside of a `gdalinfo` band output.

    Args:
        bands: Bands to search
        color: Color to search, eg Red, Green, Gray

    Returns:
       Band if it exists, None otherwise
    """
    for band in bands:
        if band["colorInterpretation"] == color:
            return band
    return None


def get_alpha_band_args(band: GdalInfoBand, preset: str | None = None) -> list[str]:
    """Return GDAL args for alpha and NIR bands (band 5 as alpha, else as NIR)."""
    # If RGBNIR_ZSTD preset, only add alpha band if it's band 5, otherwise assume it's mislabelled NIR band
    if preset == CompressionPreset.RGBNIR_ZSTD.value:
        if band["band"] == 5:
            return ["-b", str(band["band"])]
        return ["-b", str(band["band"]), f"-colorinterp_{str(band["band"])}", "nir"]
    return ["-b", str(band["band"])]


def get_gray_band_args(band: GdalInfoBand, preset: str | None = None) -> list[str]:
    """Return GDAL args for gray band (single or expanded to RGB)."""

    band_grey_index = str(band["band"])
    if preset == CompressionPreset.DEM_LERC.value:
        # return single band if DEM/DSM
        return ["-b", band_grey_index]
    # Grey scale imagery, set R,G and B to just the grey_band
    return ["-b", band_grey_index, "-b", band_grey_index, "-b", band_grey_index]


def get_palette_band_args(band: GdalInfoBand, file: str) -> list[str]:
    """Return GDAL args for palette band (expand to rgb or rgba)."""
    if colour_table := band["colorTable"]:
        palette_channels = len(colour_table["entries"][0])
        if palette_channels in (3, 4):
            return ["-expand", "rgba" if palette_channels == 4 else "rgb"]
        get_log().error(
            "unknown_palette_band_type",
            palette_channels=palette_channels,
            first_entry=colour_table["entries"][0],
            path=file,
        )
        raise RuntimeError("unknown_palette_band_type")
    get_log().error("palette_band_missing_colorTable", path=file)
    raise RuntimeError("palette_band_missing_colorTable")


def get_rgb_bands_args(bands: list[GdalInfoBand]) -> list[str]:
    """Return GDAL args for RGB bands (bands 1,2,3)."""
    band_red = find_band(bands, "Red")
    band_green = find_band(bands, "Green")
    band_blue = find_band(bands, "Blue")

    missing = [
        color_interp for color_interp, band in [("Red", band_red), ("Green", band_green), ("Blue", band_blue)] if band is None
    ]

    if band_red is None or band_green is None or band_blue is None:
        get_log().error(
            "gdal_info_bands_failed", band_red=band_red is None, band_green=band_green is None, band_blue=band_blue is None
        )
        raise RuntimeError(f"missing_expected_rgb_bands: {', '.join(missing)}")

    return ["-b", str(band_red["band"]), "-b", str(band_green["band"]), "-b", str(band_blue["band"])]


def get_gdal_band_offset(file: str, info: GdalInfo | None = None, preset: str | None = None) -> list[str]:
    """Get the banding parameters for a `gdal_translate` command.

    Args:
        file: file to check
        info: optional precomputed gdalinfo
        preset: "dem_lerc" preset used to differentiate single band elevation tiffs from single band historical imagery,
                "rgbnir_zstd" preset used to identify NIR

    Returns:
        list of band mappings eg "-b 1 -b 1 -b 1"
    """
    if info is None:
        info = gdal_info(file)

    bands = info["bands"]

    extra_args: list[str] = []
    band_nir_arg: list[str] = []

    if band_alpha := find_band(bands, "Alpha"):
        extra_args.extend(get_alpha_band_args(band_alpha, preset))

    if band_grey := find_band(bands, "Gray"):
        return get_gray_band_args(band_grey, preset) + extra_args

    if band_palette := find_band(bands, "Palette"):
        return get_palette_band_args(band_palette, file)

    rgb_bands = get_rgb_bands_args(bands)

    # Add NIR band if required
    if preset == CompressionPreset.RGBNIR_ZSTD.value:
        if (band_nir := find_band(bands, "NIR")) or (band_nir := find_band(bands, "Undefined")):
            band_nir_arg.extend(["-b", str(band_nir["band"]), f"-colorinterp_{str(band_nir["band"])}", "nir"])

    return rgb_bands + band_nir_arg + extra_args


def get_gdal_band_type(file: str, info: GdalInfo | None = None) -> str:
    """Get the band type of the first band.

    Args:
        file: file to check
        info: optional precomputed gdalinfo

    Returns:
        band type
    """
    if info is None:
        info = gdal_info(file)

    bands = info["bands"]
    return bands[0]["type"]
