from typing import cast

from scripts.gdal.gdalinfo import GdalInfo, GdalInfoBand


def fake_gdal_info() -> GdalInfo:
    return cast(GdalInfo, {})


def add_band(
    gdalinfo: GdalInfo,
    color_interpretation: str | None = None,
    no_data_value: int | None = None,
    band_type: str | None = None,
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


def add_palette_band(gdalinfo: GdalInfo, colour_table_entries: list[list[int]], no_data_value: str | None = None) -> None:
    if gdalinfo.get("bands", None) is None:
        gdalinfo["bands"] = []

    gdalinfo["bands"].append(
        cast(
            GdalInfoBand,
            {
                "band": len(gdalinfo["bands"]) + 1,
                "colorInterpretation": "Palette",
                "noDataValue": no_data_value,
                "colorTable": {"palette": "RGB", "count": len(colour_table_entries), "entries": colour_table_entries},
            },
        )
    )
