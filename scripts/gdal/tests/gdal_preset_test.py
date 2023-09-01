from scripts.gdal.gdal_preset import get_cutline_command, get_gdal_command


def test_preset_webp() -> None:
    gdal_command = get_gdal_command("webp", epsg="2193")

    # Basic cog creation
    assert "COG" in gdal_command
    assert "blocksize=512" in gdal_command
    assert "num_threads=all_cpus" in gdal_command
    assert "bigtiff=no" in gdal_command

    # Webp lossless
    assert "compress=webp" in gdal_command
    assert "quality=100" in gdal_command

    # Webp overviews
    assert "overview_compress=webp" in gdal_command
    assert "overview_resampling=lanczos" in gdal_command
    assert "overview_quality=90" in gdal_command

    assert "EPSG:2193" in gdal_command


def test_preset_lzw() -> None:
    gdal_command = get_gdal_command("lzw", epsg="2193")

    # Basic cog creation
    assert "COG" in gdal_command
    assert "blocksize=512" in gdal_command
    assert "num_threads=all_cpus" in gdal_command
    assert "bigtiff=no" in gdal_command

    # LZW compression
    assert "compress=lzw" in gdal_command
    assert "predictor=2" in gdal_command

    # Webp overviews
    assert "overview_compress=webp" in gdal_command
    assert "overview_resampling=lanczos" in gdal_command
    assert "overview_quality=90" in gdal_command

    assert "EPSG:2193" in gdal_command


def test_preset_dem_lerc() -> None:
    gdal_command = get_gdal_command("dem_lerc", epsg="2193")
    # Basic cog creation
    assert "COG" in gdal_command
    assert "blocksize=512" in gdal_command
    assert "num_threads=all_cpus" in gdal_command
    assert "bigtiff=no" in gdal_command

    # LERC compression
    assert "compress=lerc" in gdal_command
    assert "max_z_error=0.001" in gdal_command

    # No webp overviews
    assert "overview_compress=webp" not in gdal_command
    assert "overview_resampling=lanczos" not in gdal_command
    assert "overview_quality=90" not in gdal_command

    assert "EPSG:2193" in gdal_command


def test_cutline_params() -> None:
    gdal_command = get_cutline_command("cutline.fgb")

    assert "-cutline" in gdal_command
    assert "cutline.fgb" in gdal_command
    assert "-dstalpha" in gdal_command
