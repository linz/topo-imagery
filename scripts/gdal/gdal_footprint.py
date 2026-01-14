import os
from decimal import Decimal

from scripts.files.files_helper import get_file_name_from_path
from scripts.gdal.gdal_commands import get_footprint_command
from scripts.gdal.gdal_helper import run_gdal

SUFFIX_FOOTPRINT = "_footprint.geojson"


def create_footprint(
    source: str,
    target_dir: str,
    gsd: Decimal,
    preset: str,
) -> str:
    """Generate a footprint from a TIFF file.
    https://gdal.org/en/stable/programs/gdal_footprint.html

    Args:
        source: TIFF path to generate the footprint from
        target_dir: Directory path to save the footprint
        gsd: Ground Sample Distance in meters

    Returns:
        The path to the generated footprint
    """
    file_prefix = get_file_name_from_path(source)
    footprint_path = os.path.join(target_dir, file_prefix + SUFFIX_FOOTPRINT)
    run_gdal(
        get_footprint_command(gsd, preset),
        source,
        footprint_path,
    )
    return footprint_path
