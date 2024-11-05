import os
from datetime import datetime
from typing import Callable

from scripts.stac.imagery.item import STACAsset, STACProcessing, STACProcessingSoftware
from scripts.stac.util.checksum import multihash_as_hex


def fixed_now_function(now: datetime) -> Callable[[], datetime]:
    def func() -> datetime:
        return now

    return func


def any_stac_asset() -> STACAsset:
    return STACAsset(
        **{
            "href": "any href",
            "file:checksum": "any checksum",
            "created": "any created datetime",
            "updated": "any updated datetime",
        }
    )


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


def any_multihash_as_hex() -> str:
    return multihash_as_hex(os.urandom(64))
