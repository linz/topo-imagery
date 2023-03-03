from typing import Optional, cast

from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand


def fake_gdal_info() -> GdalInfo:
    return cast(GdalInfo, {})


def add_band(
    gdalinfo: GdalInfo,
    color_interpretation: Optional[str] = None,
    no_data_value: Optional[int] = None,
    band_type: Optional[str] = None,
) -> None:
    if gdalinfo.get("bands", None) is None:
        gdalinfo["bands"] = []

    gdalinfo["bands"].append(
        cast(
            GdalInfoBand,
            {
                "band": len(gdalinfo["bands"]) + 1,
                "colorInterpretation": color_interpretation,
                "noDataValue": no_data_value,
                "type": band_type,
            },
        )
    )
