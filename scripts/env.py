import os
import subprocess


def main() -> None:
    print(os.environ)
    gdal_info = subprocess.run(
        ["gdalinfo", "/vsis3/nz-elevation/new-zealand/new-zealand/dem_1m/2193/BM35.tiff"], capture_output=True, check=True
    )
    print(gdal_info)


if __name__ == "__main__":
    main()
