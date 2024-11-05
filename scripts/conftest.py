import pytest

from scripts.stac.imagery.item import STACAsset, STACProcessing, STACProcessingSoftware


@pytest.fixture
def any_stac_asset() -> STACAsset:
    return STACAsset(
        **{
            "href": "any href",
            "file:checksum": "any checksum",
            "created": "any created datetime",
            "updated": "any updated datetime",
        }
    )


@pytest.fixture
def any_stac_processing() -> STACProcessing:
    return STACProcessing(
        **{
            "processing:datetime": "any processing datetime",
            "processing:software": STACProcessingSoftware(
                **{"gdal": "any GDAL version", "linz/topo-imagery": "any topo imagery version"}
            ),
            "processing:version": "any processing version",
        }
    )
