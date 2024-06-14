from typing import Optional

from linz_logger import get_log

from scripts.gdal.gdal_helper import gdal_info
from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand


def find_band(bands: list[GdalInfoBand], color: str) -> Optional[GdalInfoBand]:
    """Look for a specific colorInterperation inside of a `gdalinfo` band output.

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


# pylint: disable-msg=too-many-return-statements
def get_gdal_band_offset(file: str, info: Optional[GdalInfo] = None, preset: Optional[str] = None) -> list[str]:
    """Get the banding parameters for a `gdal_translate` command.

    Args:
        file: file to check
        info: optional precomputed gdalinfo
        preset: "dem_lerc" preset used to differentiate single band elevation tiffs from single band historical imagery

    Returns:
        list of band mappings eg "-b 1 -b 1 -b 1"
    """
    if info is None:
        info = gdal_info(file)

    bands = info["bands"]

    band_alpha_arg: list[str] = []
    if band_alpha := find_band(bands, "Alpha"):
        band_alpha_arg.extend(["-b", str(band_alpha["band"])])

    if band_grey := find_band(bands, "Gray"):
        band_grey_index = str(band_grey["band"])
        if preset == "dem_lerc":
            # return single band if DEM/DSM
            return ["-b", band_grey_index]
        # Grey scale imagery, set R,G and B to just the grey_band
        return ["-b", band_grey_index, "-b", band_grey_index, "-b", band_grey_index] + band_alpha_arg

    if band_palette := find_band(bands, "Palette"):
        if colour_table := band_palette["colorTable"]:
            palette_channels = len(colour_table["entries"][0])
            if palette_channels == 4:
                return ["-expand", "rgba"]
            if palette_channels == 3:
                return ["-expand", "rgb"]
            get_log().error(
                "unknown_palette_band_type",
                palette_channels=palette_channels,
                first_entry=colour_table["entries"][0],
                path=file,
            )
            raise RuntimeError("unknown_palette_band_type")
        get_log().error("palette_band_missing_colorTable", path=file)
        raise RuntimeError("palette_band_missing_colorTable")

    band_red = find_band(bands, "Red")
    band_green = find_band(bands, "Green")
    band_blue = find_band(bands, "Blue")

    if band_red is None or band_green is None or band_blue is None:
        get_log().warn(
            "gdal_info_bands_failed", band_red=band_red is None, band_green=band_green is None, band_blue=band_blue is None
        )

        # Not enough bands for RGB assume it is grey scale
        if len(bands) < 3:
            return ["-b", "1", "-b", "1", "-b", "1"] + band_alpha_arg

        # Could be RGB assume it is RGB
        return ["-b", "1", "-b", "2", "-b", "3"] + band_alpha_arg

    return ["-b", str(band_red["band"]), "-b", str(band_green["band"]), "-b", str(band_blue["band"])] + band_alpha_arg


def get_gdal_band_type(file: str, info: Optional[GdalInfo] = None) -> str:
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
