import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from scripts.files.files_helper import get_file_name_from_path
from scripts.gdal.gdal_helper import GDALExecutionException, get_srs, run_gdal
from scripts.gdal.gdalinfo import gdal_info
from scripts.tile.tile_index import Point, TileIndexException, get_tile_name


class FileCheckErrorType(str, Enum):
    GDAL_INFO = "gdalinfo"
    NO_DATA = "nodata"
    BANDS = "bands"
    TILE_ALIGNMENT = "tile_alignment"
    SRS = "srs"
    COLOR = "color"


class FileCheck:
    def __init__(
        self,
        path: str,
        scale: int,
        srs: Optional[bytes] = None,
    ) -> None:
        self.path = path
        self.scale = scale
        self.errors: List[Dict[str, Any]] = []
        self._valid = True
        self._gdalinfo: Dict[Any, Any] = {}
        self._srs = srs

    def get_gdalinfo(self) -> Optional[Dict[Any, Any]]:
        if self.is_error_type(FileCheckErrorType.GDAL_INFO):
            return None
        if not self._gdalinfo:
            try:
                self._gdalinfo = gdal_info(self.path)
            except json.JSONDecodeError as jde:
                self.add_error(error_type=FileCheckErrorType.GDAL_INFO, error_message=f"parsing result issue: {str(jde)}")
            except GDALExecutionException as gee:
                self.add_error(error_type=FileCheckErrorType.GDAL_INFO, error_message=f"failed: {str(gee)}")
            except Exception as e:  # pylint: disable=broad-except
                self.add_error(error_type=FileCheckErrorType.GDAL_INFO, error_message=f"error(s): {str(e)}")
        return self._gdalinfo

    def add_error(
        self, error_type: FileCheckErrorType, error_message: str, custom_fields: Optional[Dict[str, str]] = None
    ) -> None:
        if not custom_fields:
            custom_fields = {}
        self.errors.append({"type": error_type, "message": error_message, **custom_fields})
        self._valid = False

    def is_valid(self) -> bool:
        return self._valid

    def is_error_type(self, error_type: str) -> bool:
        for error in self.errors:
            if error["error_type"] == error_type:
                return True
        return False

    def check_no_data(self, gdalinfo: Dict[Any, Any]) -> None:
        """Add an error if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands"."""
        bands = gdalinfo["bands"]
        if "noDataValue" in bands[0]:
            current_nodata_val = bands[0]["noDataValue"]
            if current_nodata_val != 255:
                self.add_error(
                    error_type=FileCheckErrorType.NO_DATA,
                    error_message="noDataValue is not 255",
                    custom_fields={"current": f"{int(current_nodata_val)}"},
                )
        else:
            self.add_error(error_type=FileCheckErrorType.NO_DATA, error_message="noDataValue not set")

    def check_band_count(self, gdalinfo: Dict[Any, Any]) -> None:
        """Add an error if there is no exactly 3 bands found."""
        bands = gdalinfo["bands"]
        bands_num = len(bands)
        if bands_num != 3:
            self.add_error(
                error_type=FileCheckErrorType.BANDS,
                error_message="bands count is not 3",
                custom_fields={"count": f"{int(bands_num)}"},
            )

    def check_srs(self, gdalsrsinfo_tif: bytes) -> None:
        """Add an error if gdalsrsinfo and gdalsrsinfo_tif values are different.

        Args:
            gdalsrsinfo_tif (str): Value returned by gdalsrsinfo for the tif as a string.
        """
        if not self._srs:
            self._srs = get_srs()
        if gdalsrsinfo_tif != self._srs:
            self.add_error(error_type=FileCheckErrorType.SRS, error_message="different srs")

    def check_color_interpretation(self, gdalinfo: Dict[Any, Any]) -> None:
        """Add an error if the colors don't match RGB.

        Args:
            gdalinfo (Dict[str, Any]): JSON returned by gdalinfo as a Python Dictionary.
        """
        bands = gdalinfo["bands"]
        missing_bands = []
        band_colour_ints = {1: "Red", 2: "Green", 3: "Blue"}
        n = 1
        for band in bands:
            colour_int = band["colorInterpretation"]
            if n in band_colour_ints:
                if colour_int != band_colour_ints[n]:
                    missing_bands.append(f"band {n} {colour_int}")
            else:
                missing_bands.append(f"band {n} {colour_int}")
            n += 1
        if missing_bands:
            missing_bands.sort()
            self.add_error(
                error_type=FileCheckErrorType.COLOR,
                error_message="unexpected color interpretation bands",
                custom_fields={"missing": f"{', '.join(missing_bands)}"},
            )

    def check_tile_and_rename(self, gdalinfo: Dict[Any, Any]) -> None:
        origin = Point(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])
        try:
            tile_name = get_tile_name(origin, self.scale)
            if not tile_name == get_file_name_from_path(self.path):
                new_path = os.path.join(os.path.dirname(self.path), tile_name + ".tiff")
                os.rename(self.path, new_path)
                self.path = new_path
        except TileIndexException as tie:
            self.add_error(FileCheckErrorType.TILE_ALIGNMENT, error_message=f"{tie}")

    def validate(self) -> bool:
        gdalinfo = self.get_gdalinfo()
        if gdalinfo:
            self.check_tile_and_rename(gdalinfo)
            self.check_no_data(gdalinfo)
            self.check_band_count(gdalinfo)
            self.check_color_interpretation(gdalinfo)

            gdalsrsinfo_tif_command = ["gdalsrsinfo", "-o", "wkt"]
            try:
                gdalsrsinfo_tif_result = run_gdal(gdalsrsinfo_tif_command, self.path)
                self.check_srs(gdalsrsinfo_tif_result.stdout)
            except GDALExecutionException as gee:
                self.add_error(error_type=FileCheckErrorType.SRS, error_message=f"not checked: {str(gee)}")
        return self.is_valid()
