from datetime import datetime
from os import urandom
from typing import Callable

from pystac import Asset

from scripts.stac.imagery.asset import create_visual_asset
from scripts.stac.imagery.item import STACProcessing, STACProcessingSoftware
from scripts.stac.util.checksum import multihash_as_hex


def fixed_now_function(now: datetime) -> Callable[[], datetime]:
    def func() -> datetime:
        return now

    return func


def any_visual_asset() -> Asset:
    return create_visual_asset(href="any href", checksum="any checksum", created="any created datetime")


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
    return multihash_as_hex(urandom(64))
