import os

from scripts.gdal.gdal_helper import gdal_info


def main() -> None:
    print(os.environ)
    # gdal_info = subprocess.run(
    #     ["gdalinfo", "/vsis3/nz-elevation/new-zealand/new-zealand/dem_1m/2193/BM35.tiff"], capture_output=True, check=True
    # )
    gdalinfo = gdal_info("/vsis3/nz-elevation/new-zealand/new-zealand/dem_1m/2193/BM35.tiff")
    print(gdalinfo)


if __name__ == "__main__":
    main()
