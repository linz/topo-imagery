import os
from datetime import datetime
from typing import Any, Callable

from pystac import Asset, Item, RelType

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files import fs
from scripts.files.fs import modified
from scripts.stac.imagery.links import ComparableLink
from scripts.stac.util import checksum
from scripts.stac.util.stac_extensions import StacExtensions

BoundingBox = tuple[float, float, float, float]


class ImageryItem(Item):
    def __init__(  # pylint: disable-msg=too-many-arguments
        self,
        id_: str,
        geometry: dict[str, Any],
        bbox: BoundingBox,
        now: Callable[[], datetime],
        start_datetime: datetime,
        end_datetime: datetime,
        href: str,
        collection_id: str,
    ):
        file_content = fs.read(href)
        multihash = checksum.multihash_as_hex(file_content)
        file_modified_datetime = format_rfc_3339_datetime_string(modified(href))

        visual_asset = Asset(
            os.path.join(".", os.path.basename(href)),
            media_type="image/tiff; application=geotiff; profile=cloud-optimized",
        )
        visual_asset.__setattr__("file:checksum", multihash)
        visual_asset.__setattr__("created", file_modified_datetime)
        visual_asset.__setattr__("updated", file_modified_datetime)

        now_string = format_rfc_3339_datetime_string(now())

        super().__init__(
            id_,
            geometry,
            bbox=list(bbox),
            datetime=None,
            properties={
                "created": now_string,
                "updated": now_string,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
            },
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            stac_extensions=[StacExtensions.file.value],
            collection=collection_id,
            assets={"visual": visual_asset},
        )
        self.add_links(
            [
                ComparableLink(RelType.SELF, f"./{id_}.json", "application/json"),
                ComparableLink(RelType.COLLECTION, "./collection.json", "application/json"),
                ComparableLink(RelType.PARENT, "./collection.json", "application/json"),
            ]
        )
