import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from linz_logger import get_log

from scripts.files.files_helper import get_file_name_from_path
from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal
from scripts.gdal.gdalinfo import GdalInfo, gdal_info, get_origin
from scripts.tile.tile_index import TileIndexException, get_tile_name


class FileTiffErrorType(str, Enum):
    GDAL_INFO = "gdalinfo"
    NO_DATA = "nodata"
    BANDS = "bands"
    TILE_ALIGNMENT = "tile_alignment"
    SRS = "srs"
    COLOR = "color"


class FileTiff:
    """Wrapper to carry information about the TIFF file."""

    def __init__(
        self,
        path: str,
        preset: Optional[str] = None,
    ) -> None:
        self._path_original = path
        self._path_standardised = ""
        self._errors: List[Dict[str, Any]] = []
        self._scale = 0
        self._gdalinfo: Optional[GdalInfo] = None
        self._srs: Optional[bytes] = None
        if preset == "dem_lerc":
            self._tiff_type = "DEM"
        else:
            self._tiff_type = "Imagery"

    def set_srs(self, srs: bytes) -> None:
        """Set the Spatial Reference System returned by `gdalsrsinfo` for the TIFF.

        Args:
            srs: the srs in bytes

        Example:
            ```
            $ gdalsrsinfo RGB_1000_CC16_4127_2013.tiff

            PROJ.4 : +proj=tmerc +lat_0=0 +lon_0=173 +k=0.9996 +x_0=1600000 +y_0=10000000 +ellps=GRS80
            +towgs84=0,0,0,0,0,0,0 +units=m +no_defs

            OGC WKT2:2018 :
            PROJCRS["NZGD2000 / New Zealand Transverse Mercator 2000",
                BASEGEOGCRS["NZGD2000",
                    DATUM["New Zealand Geodetic Datum 2000",
                        ELLIPSOID["GRS 1980",6378137,298.257222101,
                            LENGTHUNIT["metre",1]]],
                    PRIMEM["Greenwich",0,
                        ANGLEUNIT["degree",0.0174532925199433]],
                    ID["EPSG",4167]],
                CONVERSION["New Zealand Transverse Mercator 2000",
                    METHOD["Transverse Mercator",
                        ID["EPSG",9807]],
                    PARAMETER["Latitude of natural origin",0,
                        ANGLEUNIT["degree",0.0174532925199433],
                        ID["EPSG",8801]],
                    PARAMETER["Longitude of natural origin",173,
                        ANGLEUNIT["degree",0.0174532925199433],
                        ID["EPSG",8802]],
                    PARAMETER["Scale factor at natural origin",0.9996,
                        SCALEUNIT["unity",1],
                        ID["EPSG",8805]],
                    PARAMETER["False easting",1600000,
                        LENGTHUNIT["metre",1],
                        ID["EPSG",8806]],
                    PARAMETER["False northing",10000000,
                        LENGTHUNIT["metre",1],
                        ID["EPSG",8807]]],
                CS[Cartesian,2],
                    AXIS["northing (N)",north,
                        ORDER[1],
                        LENGTHUNIT["metre",1]],
                    AXIS["easting (E)",east,
                        ORDER[2],
                        LENGTHUNIT["metre",1]],
                USAGE[
                    SCOPE["Engineering survey, topographic mapping."],
                    AREA["New Zealand - North Island, South Island, Stewart Island - onshore."],
                    BBOX[-47.33,166.37,-34.1,178.63]],
                ID["EPSG",2193]
        ```
        """
        self._srs = srs

    def set_scale(self, scale: int) -> None:
        """Set the cartographic scale of the TIFF.

        Args:
            scale: the scale as `int` between tile_index.GRID_SIZES
        """
        self._scale = scale

    def set_path_standardised(self, path: str) -> None:
        """Set the standardised file path.

        Args:
            path: the path to the standardised file

        Example:
            ```
            >>> file_tiff.set_path_standardised("/output/BY12_5000_0805.tiff")
            ```
        """
        self._path_standardised = path

    def get_gdalinfo(self) -> Optional[GdalInfo]:
        """Get the `gdalinfo` output for the file.
        Run gdalinfo if not already ran.

        Returns:
            the `gdalinfo` output
        """
        # FIXME: Should not return None but not try running `gdalinfo` if there has already been an error
        if self.is_error_type(FileTiffErrorType.GDAL_INFO):
            return None
        if not self._gdalinfo:
            try:
                self._gdalinfo = gdal_info(self._path_standardised, False)
            except json.JSONDecodeError as jde:
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"parsing result issue: {str(jde)}")
            except GDALExecutionException as gee:
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"failed: {str(gee)}")
            except Exception as e:  # pylint: disable=broad-except
                self.add_error(error_type=FileTiffErrorType.GDAL_INFO, error_message=f"error(s): {str(e)}")
        return self._gdalinfo

    def set_gdalinfo(self, gdalinfo: GdalInfo) -> None:
        """Set the `gdalinfo` output for the file.

        Args:
            gdalinfo: the `gdalinfo` output
        """
        self._gdalinfo = gdalinfo

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get the Non Visual QA errors.

        Returns:
            a list of errors
        """
        return self._errors

    def get_path_original(self) -> str:
        """Get the path of the original (non standardised) file.

        Returns:
            a file path
        """
        return self._path_original

    def get_path_standardised(self) -> str:
        """Get the path of the standardised file.

        Returns:
            a file path
        """
        return self._path_standardised

    def add_error(
        self, error_type: FileTiffErrorType, error_message: str, custom_fields: Optional[Dict[str, str]] = None
    ) -> None:
        """Add an error in Non Visual QA errors list.

        Args:
            error_type: the type of the error
            error_message: the message of the error
            custom_fields: some custom properties. Defaults to None.
        """
        if not custom_fields:
            custom_fields = {}
        self._errors.append({"type": error_type, "message": error_message, **custom_fields})

    def is_valid(self) -> bool:
        """Check if the file is set to valid or not.

        Returns:
            true if _errors is empty
        """
        if len(self._errors) == 0:
            return True
        return False

    def is_error_type(self, error_type: FileTiffErrorType) -> bool:
        """Check if the file has a Non Visual QA error of the type `error_type`.

        Args:
            error_type: one of the value of `FileTiffErrorType`

        Returns:
            True if the the `error_type` is found
        """
        for error in self._errors:
            if error["type"] == error_type:
                return True
        return False

    def check_no_data(self, gdalinfo: GdalInfo) -> None:
        """Add a Non Visual QA error if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands".

        Args:
            gdalinfo: `gdalinfo` output
        """
        bands = gdalinfo["bands"]
        if len(bands) == 4 and bands[3]["colorInterpretation"] == "Alpha":
            return
        if "noDataValue" in bands[0]:
            current_nodata_val = bands[0]["noDataValue"]
            if current_nodata_val != 255:
                self.add_error(
                    error_type=FileTiffErrorType.NO_DATA,
                    error_message="noDataValue is not 255",
                    custom_fields={"current": f"{current_nodata_val}"},
                )

    def is_no_data(self, gdalinfo: GdalInfo) -> bool:
        """Check if the bands have a "noDataValue" set.

        Args:
            gdalinfo: `gdalinfo` output

        Returns:
            True if a `noDataValue` is found
        """
        bands = gdalinfo["bands"]
        # 0 in noDataValue can return false unless specific here about None
        if "noDataValue" in bands[0] and bands[0]["noDataValue"] is not None:
            return True
        return False

    def check_band_count(self, gdalinfo: GdalInfo) -> None:
        """Add a Non Visual QA error if there is not exactly 3 or 4 bands found.

        Args:
            gdalinfo: `gdalinfo` output
        """
        bands_num = 3
        if self._tiff_type == "DEM":
            bands_num = 1

        bands = gdalinfo["bands"]
        if len(bands) == bands_num + 1:
            if bands[bands_num]["colorInterpretation"] == "Alpha":
                bands_num += 1
        if len(bands) != bands_num:
            self.add_error(
                error_type=FileTiffErrorType.BANDS,
                error_message=f"bands count is not {bands_num}",
                custom_fields={"count": f"{int(bands_num)}"},
            )

    def check_srs(self, gdalsrsinfo_tif: bytes) -> None:
        """Add a Non Visual QA error if gdalsrsinfo and gdalsrsinfo_tif values are different.

        Args:
            gdalsrsinfo_tif : value returned by gdalsrsinfo for the tif as a string
        """
        if self._srs:
            if gdalsrsinfo_tif != self._srs:
                self.add_error(error_type=FileTiffErrorType.SRS, error_message="different srs")
        else:
            self.add_error(error_type=FileTiffErrorType.SRS, error_message="srs not defined")

    def check_color_interpretation(self, gdalinfo: GdalInfo) -> None:
        """Add a Non Visual QA error if the colors don't match RGB.

        Args:
            gdalinfo: `gdalinfo` output
        """
        bands = gdalinfo["bands"]
        missing_bands = []
        band_colour_ints = {1: "Red", 2: "Green", 3: "Blue"}
        optional_colour_ints = {4: "Alpha"}
        if self._tiff_type == "DEM":
            band_colour_ints = {1: "Gray"}
            optional_colour_ints = {2: "Alpha"}
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
        """Validate the TIFF origin within its scale and standardise the filename.

        Args:
            gdalinfo: `gdalinfo` output
        """
        if self._scale > 0:
            origin = get_origin(gdalinfo)
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
        """Run the Non Visual QA checks.

        Returns:
            True if there is no error
        """

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
