from imagery.gdal.gdalinfo import format_wkt


def test_format_wkt() -> None:
    gdalinfo_wkt_output = '"NZGD2000 / New Zealand Transverse Mercator 2000",\n    BASEGEOGCRS["NZGD2000",\n        DAT'
    gdalinfo_wkt_formatted = format_wkt(gdalinfo_wkt_output)

    assert gdalinfo_wkt_formatted == "'NZGD2000 / New Zealand Transverse Mercator 2000', BASEGEOGCRS['NZGD2000', DAT"
