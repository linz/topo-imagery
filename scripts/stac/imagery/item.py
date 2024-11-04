from typing import Any, TypedDict

from scripts.stac.link import Link, Relation
from scripts.stac.util.STAC_VERSION import STAC_VERSION
from scripts.stac.util.media_type import StacMediaType
from scripts.stac.util.stac_extensions import StacExtensions

STACAsset = TypedDict("STACAsset", {"href": str, "file:checksum": str, "created": str, "updated": str})

STACProcessingSoftware = TypedDict("STACProcessingSoftware", {"gdal": str, "linz/topo-imagery": str})
"""STAC Processing extension LINZ specific fields"""

STACProcessing = TypedDict(
    "STACProcessing",
    {
        "processing:datetime": str,
        "processing:software": STACProcessingSoftware,
        "processing:version": str,
    },
)
"""Some of the STAC processing extension fields are not declared in this TypedDict 
(https://github.com/stac-extensions/processing?tab=readme-ov-file#fields)
"""


class ImageryItem:
    stac: dict[str, Any]

    def __init__(self, id_: str, now_string: str, stac_asset: STACAsset, stac_processing: STACProcessing) -> None:
        self.stac = {
            "type": "Feature",
            "stac_version": STAC_VERSION,
            "id": id_,
            "links": [Link(path=f"./{id_}.json", rel=Relation.SELF, media_type=StacMediaType.GEOJSON).stac],
            "assets": {"visual": {**stac_asset, "type": "image/tiff; application=geotiff; profile=cloud-optimized"}},
            "stac_extensions": [StacExtensions.file.value, StacExtensions.processing.value],
            "properties": {"created": now_string, "updated": now_string, **stac_processing},
        }

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        """Update the Item `start_datetime` and `end_datetime` property.

        Args:
            start_datetime: a start date in `YYYY-MM-DD` format
            end_datetime: a end date in `YYYY-MM-DD` format
        """
        self.stac.setdefault("properties", {})
        self.stac["properties"]["start_datetime"] = start_datetime
        self.stac["properties"]["end_datetime"] = end_datetime
        self.stac["properties"]["datetime"] = None

    # FIXME: redefine the 'Any'
    def update_spatial(self, geometry: dict[str, Any], bbox: tuple[float, ...]) -> None:
        """Update the `geometry` and `bbox` (bounding box) of the Item.

        Args:
            geometry: a geometry
            bbox: a bounding box
        """
        self.stac["geometry"] = geometry
        self.stac["bbox"] = bbox

    def add_collection(self, collection_id: str) -> None:
        """Link a Collection to the Item as its `collection` and `parent`.

        Args:
            collection_id: the id of the collection to link
        """
        self.stac["collection"] = collection_id
        self.add_link(Link(path="./collection.json", rel=Relation.COLLECTION, media_type=StacMediaType.JSON))
        self.add_link(Link(path="./collection.json", rel=Relation.PARENT, media_type=StacMediaType.JSON))

    def add_link(self, link: Link) -> None:
        self.stac["links"].append(link.stac)
