from enum import IntEnum


class EpsgNumber(IntEnum):
    NZTM_2000 = 2193
    """New Zealand Transverse Mercator 2000"""
    WGS_1984 = 4326
    """World Geodetic System 1984"""
    CITM_2000 = 3793
    """Chatham Islands Transverse Mercator 2000"""
    NZVD_2016 = 7839
    """New Zealand Vertical Datum 2016"""
