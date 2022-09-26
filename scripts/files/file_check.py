from typing import Any, Dict, List, Optional

from scripts.gdal.gdal_helper import GDALExecutionException, run_gdal


class FileCheck:
    def __init__(self, path: str, srs: bytes) -> None:
        self.path = path
        self.global_srs = srs
        self.errors: List[Dict[str, Any]] = []
        self._valid = True

    def add_error(self, error_type: str, error_message: str, custom_fields: Optional[Dict[str, str]] = None) -> None:
        if not custom_fields:
            custom_fields = {}
        self.errors.append({"type": error_type, "message": error_message, **custom_fields})
        self._valid = False

    def is_valid(self) -> bool:
        return self._valid

    def check_no_data(self, gdalinfo: Dict[str, Any]) -> None:
        """Add an error if there is no "noDataValue" or the "noDataValue" is not equal to 255 in the "bands".

        Args:
            gdalinfo (Dict[str, Any]): JSON return of gdalinfo in a Python Dictionary.
        """
        bands = gdalinfo["bands"]
        if "noDataValue" in bands[0]:
            current_nodata_val = bands[0]["noDataValue"]
            if current_nodata_val != 255:
                self.add_error(
                    error_type="nodata",
                    error_message="noDataValue is not 255",
                    custom_fields={"current": f"{int(current_nodata_val)}"},
                )
        else:
            self.add_error(error_type="nodata", error_message="noDataValue not set")

    def check_band_count(self, gdalinfo: Dict[str, Any]) -> None:
        """Add an error if there is no exactly 3 bands found.

        Args:
            gdalinfo (Dict[str, Any]): JSON returned by gdalinfo as a Python Dictionary.
        """
        bands = gdalinfo["bands"]
        bands_num = len(bands)
        if bands_num != 3:
            self.add_error(
                error_type="bands", error_message="bands count is not 3", custom_fields={"count": f"{int(bands_num)}"}
            )

    def check_srs(self, gdalsrsinfo_tif: bytes) -> None:
        """Add an error if gdalsrsinfo and gdalsrsinfo_tif values are different.

        Args:
            gdalsrsinfo (str): Value returned by gdalsrsinfo as a string.
            gdalsrsinfo_tif (str): Value returned by gdalsrsinfo for the tif as a string.
        """
        if gdalsrsinfo_tif != self.global_srs:
            self.add_error(error_type="srs", error_message="different srs")

    def check_color_interpretation(self, gdalinfo: Dict[str, Any]) -> None:
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
                error_type="color",
                error_message="unexpected color interpretation bands",
                custom_fields={"missing": f"{', '.join(missing_bands)}"},
            )

    def validate(self, gdalinfo_result: Dict[Any, Any]) -> None:
        if self.is_valid():
            self.check_no_data(gdalinfo_result)
            self.check_band_count(gdalinfo_result)
            self.check_color_interpretation(gdalinfo_result)
            gdalsrsinfo_tif_command = ["gdalsrsinfo", "-o", "wkt"]
            try:
                gdalsrsinfo_tif_result = run_gdal(gdalsrsinfo_tif_command, self.path)
                self.check_srs(gdalsrsinfo_tif_result.stdout)
            except GDALExecutionException as gee:
                self.add_error(error_type="srs", error_message=f"not checked: {str(gee)}")
