from typing import List, Optional

from linz_logger import get_log

from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand, gdal_info


def find_band(bands: List[GdalInfoBand], color: str) -> Optional[GdalInfoBand]:
    """Look for a specific colorInterperation inside of a gdalinfo band output

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


def get_gdal_band_offset(file: str, info: Optional[GdalInfo] = None) -> List[str]:
    """Get the banding parameters for a gdal_translate command

    Args:
        file: file to check
        info: optional precomputed gdalinfo

    Returns:
        list of band mappings eg "-b 1 -b 1 -b 1"
    """
    if info is None:
        info = gdal_info(file, False)

    bands = info["bands"]

    alpha_band = find_band(bands, "Alpha")
    alpha_band_info: List[str] = []
    if alpha_band:
        alpha_band_info.extend(["-b", str(alpha_band["band"])])

    # Grey scale imagery, set R,G and B to just the grey_band
    grey_band = find_band(bands, "Gray")
    if grey_band:
        grey_band_index = str(grey_band["band"])
        return ["-b", grey_band_index, "-b", grey_band_index, "-b", grey_band_index] + alpha_band_info

    band_red = find_band(bands, "Red")
    band_green = find_band(bands, "Green")
    band_blue = find_band(bands, "Blue")

    if band_red is None or band_green is None or band_blue is None:
        get_log().warn(
            "gdal_info_bands_failed", band_red=band_red is None, band_green=band_green is None, band_blue=band_blue is None
        )

        # Not enough bands for RGB assume it is grey scale
        if len(bands) < 3:
            return ["-b", "1", "-b", "1", "-b", "1"] + alpha_band_info

        # Could be RGB assume it is RGB
        return ["-b", "1", "-b", "2", "-b", "3"] + alpha_band_info

    return ["-b", str(band_red["band"]), "-b", str(band_green["band"]), "-b", str(band_blue["band"])] + alpha_band_info


def get_gdal_band_type(file: str, info: Optional[GdalInfo] = None) -> str:
    """Get the band type to determine the bit number

    Args:
        file: file to check
        info: optional precomputed gdalinfo

    Returns:
        band type
    """
    if info is None:
        info = gdal_info(file, False)

    bands = info["bands"]
    return bands[0]["type"]
