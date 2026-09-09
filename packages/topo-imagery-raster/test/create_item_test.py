from typing import cast

from topo_imagery_gdal.gdal.gdalinfo import GdalInfo
from topo_imagery_raster.create_item import create_item_from_tiff
from topo_imagery_stac.testing.helpers import any_epoch_datetime_string


def test_should_derive_spatial_extents_from_gdalinfo() -> None:
    """`create_item_from_tiff` converts a `gdalinfo` result into the geometry and bbox of the Item."""
    gdalinfo_result: GdalInfo = cast(
        GdalInfo, {"wgs84Extent": {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}}
    )

    item = create_item_from_tiff(
        "./e2e/data/empty.tiff",
        any_epoch_datetime_string(),
        any_epoch_datetime_string(),
        "any collection id",
        "any GDAL version",
        any_epoch_datetime_string(),
        gdalinfo_result,
    )

    assert item.stac["geometry"] == {"type": "Polygon", "coordinates": [[[0, 1], [1, 1], [1, 0], [0, 0]]]}
    assert item.stac["bbox"] == (0.0, 0.0, 1.0, 1.0)
