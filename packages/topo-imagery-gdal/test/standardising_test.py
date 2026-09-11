from decimal import Decimal

from pytest import raises
from pytest_subtests import SubTests
from topo_imagery_common.epsg import EpsgNumber
from topo_imagery_gdal.gdal.gdal_presets import CompressionPreset, DataType
from topo_imagery_gdal.standardising import StandardisingConfig


def standardising_config(preset: str, data_type: str) -> StandardisingConfig:
    return StandardisingConfig(
        gdal_preset=preset,
        source_epsg=EpsgNumber.NZTM_2000.value,
        target_epsg=EpsgNumber.NZTM_2000.value,
        gsd=Decimal("0.1"),
        create_footprints=False,
        simplify_footprints=False,
        cutline=None,
        data_type=data_type,
    )


def test_config_defaults_to_uint8() -> None:
    config = StandardisingConfig(
        gdal_preset=CompressionPreset.WEBP.value,
        source_epsg=EpsgNumber.NZTM_2000.value,
        target_epsg=EpsgNumber.NZTM_2000.value,
        gsd=Decimal("0.1"),
        create_footprints=False,
        simplify_footprints=False,
        cutline=None,
    )

    assert config.data_type == DataType.UINT8.value


def test_config_allows_high_bit_depth_rgbnir(subtests: SubTests) -> None:
    for data_type in DataType:
        with subtests.test(msg=f"{data_type.value} is valid with {CompressionPreset.RGBNIR_ZSTD.value}"):
            config = standardising_config(CompressionPreset.RGBNIR_ZSTD.value, data_type.value)

            assert config.data_type == data_type.value


def test_config_allows_uint8_for_any_preset(subtests: SubTests) -> None:
    for preset in CompressionPreset:
        with subtests.test(msg=f"{DataType.UINT8.value} is valid with {preset.value}"):
            config = standardising_config(preset.value, DataType.UINT8.value)

            assert config.data_type == DataType.UINT8.value


def test_config_rejects_high_bit_depth_for_other_presets(subtests: SubTests) -> None:
    for preset in [preset for preset in CompressionPreset if preset != CompressionPreset.RGBNIR_ZSTD]:
        for data_type in [DataType.UINT16, DataType.UINT32]:
            with subtests.test(msg=f"{data_type.value} is invalid with {preset.value}"):
                with raises(ValueError, match=f"is only supported with the {CompressionPreset.RGBNIR_ZSTD.value} preset"):
                    standardising_config(preset.value, data_type.value)


def test_config_rejects_unknown_data_type() -> None:
    with raises(ValueError, match="Unsupported data type: int16"):
        standardising_config(CompressionPreset.RGBNIR_ZSTD.value, "int16")
