from typing import List

from linz_logger import get_log

GDAL_PRESET_LZW = [
    "gdal_translate",
    "-q",
    "-scale",
    "0",
    "255",
    "0",
    "254",
    "-a_srs",
    "EPSG:2193",
    "-a_nodata",
    "255",
    "-b",
    "1",
    "-b",
    "2",
    "-b",
    "3",
    "-of",
    "COG",
    "-co",
    "compress=lzw",
    "-co",
    "num_threads=all_cpus",
    "-co",
    "predictor=2",
    "-co",
    "overview_compress=webp",
    "-co",
    "bigtiff=yes",
    "-co",
    "overview_resampling=lanczos",
    "-co",
    "blocksize=512",
    "-co",
    "overview_quality=90",
    "-co",
    "sparse_ok=true",
]

GDAL_PRESET_WEBP = [
    "gdal_translate",
    "-q",
    "-a_srs",
    "EPSG:2193",
    "-of",
    "COG",
    "-co",
    "compress=webp",
    "-co",
    "num_threads=all_cpus",
    "-co",
    "quality=100",
    "-co",
    "overview_compress=webp",
    "-co",
    "bigtiff=yes",
    "-co",
    "overview_resampling=lanczos",
    "-co",
    "blocksize=512",
    "-co",
    "overview_quality=90",
    "-co",
    "sparse_ok=true",
]

GDAL_PRESET_GRAY_WEBP = [
    "gdal_translate",
    "-q",
    "-a_srs",
    "EPSG:2193",
    "-b",
    "1",
    "-b",
    "1",
    "-b",
    "1",
    "-a_nodata",
    "255",
    "-of",
    "COG",
    "-co",
    "compress=webp",
    "-co",
    "num_threads=all_cpus",
    "-co",
    "quality=100",
    "-co",
    "overview_compress=webp",
    "-co",
    "bigtiff=yes",
    "-co",
    "overview_resampling=lanczos",
    "-co",
    "blocksize=512",
    "-co",
    "overview_quality=90",
    "-co",
    "sparse_ok=true",
]


def get_gdal_command(preset: str) -> List[str]:
    get_log().info("gdal_preset", preset=preset)
    if preset == "lzw":
        return GDAL_PRESET_LZW
    if preset == "webp":
        return GDAL_PRESET_WEBP
    if preset == "gray_webp":
        return GDAL_PRESET_GRAY_WEBP
    raise Exception(f"Unknown GDAL preset: {preset}")
