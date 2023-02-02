import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from linz_logger import get_log

from scripts.files.files_helper import get_file_name_from_path
from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal
from scripts.gdal.gdalinfo import GdalInfo, gdal_info
from scripts.tile.tile_index import Point, TileIndexException, get_tile_name


class FileTiffErrorType(str, Enum):
    GDAL_INFO = "gdalinfo"
    NO_DATA = "nodata"
    BANDS = "bands"
    TILE_ALIGNMENT = "tile_alignment"
    SRS = "srs"
    COLOR = "color"


class FileTiff:
    """Wrapper for the TIFF files"""

    def __init__(
        self,
        path: str,
    ) -> None:
        self._path_original = path
        self._path_standardised = ""
        self._errors: List[Dict[str, Any]] = []
        self._scale = 0
        self._valid = True
        self._gdalinfo: Optional[GdalInfo] = None
        self._srs: Optional[bytes] = None

    def set_srs(self, srs: bytes) -> None:
        self._srs = srs

    def set_scale(self, scale: int) -> None:
        self._scale = scale

    def set_path_standardised(self, path: str) -> None:
        self._path_standardised = path

    def get_gdalinfo(self) -> Optional[GdalInfo]:
        if self.is_error_type(FileTiffErrorType.GDAL_INFO):
            return None
        if not self._gdalinfo:
            try:
                self._gdalinfo = gdal_info(self._path_standardised)
            except json.JSONDecodeError as jde:
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"parsing result issue: {str(jde)}")
            except GDALExecutionException as gee:
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"failed: {str(gee)}")
            except Exception as e:  # pylint: disable=broad-except
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"error(s): {str(e)}")
        return self._gdalinfo

    def get_gdalinfo_original(self) -> Optional[GdalInfo]:
        _original_gdalinfo = None
        try:
            _original_gdalinfo = gdal_info(self._path_original)
        except json.JSONDecodeError as jde:
            get_log().warning(
                "GDALINFO Original Tiff Failed",
                error_type=FileTiffErrorType.GDAL_INFO,
                error_message=f"parsing result issue: {str(jde)}",
            )
        except GDALExecutionException as gee:
            get_log().warning(
                "GDALINFO Original Tiff Failed", error_type=FileTiffErrorType.GDAL_INFO, error_message=f"failed: {str(gee)}"
            )
        except Exception as e:  # pylint: disable=broad-except
            get_log().warning(
                "GDALINFO Original Tiff Failed", error_type=FileTiffErrorType.GDAL_INFO, error_message=f"error(s): {str(e)}"
            )
        return _original_gdalinfo

    def get_errors(self) -> List[Dict[str, Any]]:
        return self._errors

    def get_path_original(self) -> str:
        return self._path_original

    def get_path_standardised(self) -> str:
        return self._path_standardised

    def add_error(
        self, error_type: FileTiffErrorType, error_message: str, custom_fields: Optional[Dict[str, str]] = None
    ) -> None:
        if not custom_fields:
            custom_fields = {}
        self._errors.append({"type": error_type, "message": error_message, **custom_fields})
        self._valid = False

    def is_valid(self) -> bool:
        return self._valid

    def is_error_type(self, error_type: str) -> bool:
        for error in self._errors:
            if error["type"] == error_type:
                return True
        return False

    def check_no_data(self, gdalinfo: GdalInfo) -> None:
        """Add an error if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands"."""
        bands = gdalinfo["bands"]
        if "noDataValue" in bands[0]:
            current_nodata_val = bands[0]["noDataValue"]
            if current_nodata_val != 255:
                self.add_error(
                    error_type=FileTiffErrorType.NO_DATA,
                    error_message="noDataValue is not 255",
                    custom_fields={"current": f"{current_nodata_val}"},
                )
        else:
            if bands[4]["colorInterpretation"] != "Alpha":
                self.add_error(error_type=FileTiffErrorType.NO_DATA, error_message="noDataValue not set")

    def check_no_data_original(self, gdalinfo: GdalInfo) -> bool:
        """return True if "noDataValue" and the "noDataValue" is not equal to 255 in the "bands"."""
        bands = gdalinfo["bands"]
        if "noDataValue" not in bands[0]:
            return False
        elif bands[0]["noDataValue"] != 255:
            return False
        return True

    def check_band_count(self, gdalinfo: GdalInfo) -> None:
        """Add an error if there is not exactly 3 bands found."""
        bands = gdalinfo["bands"]
        bands_num = 3
        for band in bands:
            if band["colorInterpretation"] == "Alpha":
                bands_num = 4
        if len(bands) != bands_num:
            self.add_error(
                error_type=FileTiffErrorType.BANDS,
                error_message=f"bands count is not {bands_num}",
                custom_fields={"count": f"{int(bands_num)}"},
            )

    def check_srs(self, gdalsrsinfo_tif: bytes) -> None:
        """Add an error if gdalsrsinfo and gdalsrsinfo_tif values are different.
        Args:
            gdalsrsinfo_tif (str): Value returned by gdalsrsinfo for the tif as a string.
        """
        if self._srs:
            if gdalsrsinfo_tif != self._srs:
                self.add_error(error_type=FileTiffErrorType.SRS, error_message="different srs")
        else:
            self.add_error(error_type=FileTiffErrorType.SRS, error_message="srs not defined")

    def check_color_interpretation(self, gdalinfo: GdalInfo) -> None:
        """Add an error if the colors don't match RGB.

        Args:
            gdalinfo (Dict[str, Any]): JSON returned by gdalinfo as a Python Dictionary.
        """
        bands = gdalinfo["bands"]
        missing_bands = []
        band_colour_ints = {1: "Red", 2: "Green", 3: "Blue"}
        optional_colour_ints = {4: "Alpha"}
        n = 1
        for band in bands:
            colour_int = band["colorInterpretation"]
            if n in band_colour_ints:
                if colour_int != band_colour_ints[n]:
                    missing_bands.append(f"band {n} {colour_int}")
            elif n in optional_colour_ints:
                if colour_int != optional_colour_ints[n]:
                    missing_bands.append(f"band {n} {colour_int}")
            else:
                missing_bands.append(f"band {n} {colour_int}")
            n += 1
        if missing_bands:
            missing_bands.sort()
            self.add_error(
                error_type=FileTiffErrorType.COLOR,
                error_message="unexpected color interpretation bands",
                custom_fields={"missing": f"{', '.join(missing_bands)}"},
            )

    def check_tile_and_rename(self, gdalinfo: GdalInfo) -> None:
        origin = Point(gdalinfo["cornerCoordinates"]["upperLeft"][0], gdalinfo["cornerCoordinates"]["upperLeft"][1])
        try:
            tile_name = get_tile_name(origin, self._scale)
            if not tile_name == get_file_name_from_path(self._path_standardised):
                new_path = os.path.join(os.path.dirname(self._path_standardised), tile_name + ".tiff")
                os.rename(self._path_standardised, new_path)
                get_log().info("renaming_file", path=new_path, old=self._path_standardised)
                self._path_standardised = new_path

        except TileIndexException as tie:
            self.add_error(FileTiffErrorType.TILE_ALIGNMENT, error_message=f"{tie}")

    def validate(self) -> bool:
        gdalinfo = self.get_gdalinfo()
        if gdalinfo:
            self.check_tile_and_rename(gdalinfo)
            self.check_no_data(gdalinfo)
            self.check_band_count(gdalinfo)
            self.check_color_interpretation(gdalinfo)

            gdalsrsinfo_tif_command = ["gdalsrsinfo", "-o", "wkt"]
            try:
                gdalsrsinfo_tif_result = run_gdal(gdalsrsinfo_tif_command, self._path_standardised)
                self.check_srs(gdalsrsinfo_tif_result.stdout)
            except GDALExecutionException as gee:
                self.add_error(error_type=FileTiffErrorType.SRS, error_message=f"not checked: {str(gee)}")
        return self.is_valid()
