import json
import typing
from typing import Any, TypedDict

from pystac import Asset, Item, Link, MediaType, RelType, StacIO
from pystac.utils import HREF

from scripts.datetimes import parse_rfc_3339_datetime
from scripts.stac.link import create_link_with_checksum
from scripts.stac.util.stac_extensions import StacExtensions

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


class ImageryItem(Item):

    def __init__(
        self,
        id_: str,
        asset: Asset,
        stac_processing: STACProcessing,
        start_datetime: str,
        end_datetime: str,
    ) -> None:
        stac_extensions = [StacExtensions.file.value, StacExtensions.processing.value]
        assets = {"visual": asset}
        properties = {"created": asset.extra_fields["created"], "updated": asset.extra_fields["updated"], **stac_processing}
        super().__init__(
            id=id_,
            geometry=None,
            bbox=None,
            datetime=None,
            stac_extensions=stac_extensions,
            assets=assets,
            properties=properties,
            start_datetime=parse_rfc_3339_datetime(start_datetime),
            end_datetime=parse_rfc_3339_datetime(end_datetime),
        )

        # Manually add the self link as pystac would force it to be absolute otherwise (requirement in STAC v1.1)
        # pystac would have use the MediaType JSON for the self link, but we want to use the GeoJSON type
        self.make_self_link_relative()

    @classmethod
    def from_file(cls, href: HREF, stac_io: StacIO | None = None) -> "ImageryItem":
        # Use pystac.Item's from_file to parse the STAC file
        item = Item.from_file(href, stac_io)
        imagery_item = cls(
            id_=item.id,
            asset=item.assets["visual"],
            stac_processing={
                "processing:datetime": item.properties["processing:datetime"],
                "processing:software": item.properties["processing:software"],
                "processing:version": item.properties["processing:version"],
            },
            start_datetime=item.properties["start_datetime"],
            end_datetime=item.properties["end_datetime"],
        )
        if item.collection_id:
            imagery_item.add_collection(item.collection_id)
        if item.geometry and item.bbox:
            imagery_item.update_spatial(item.geometry, item.bbox)
        imagery_item.make_self_link_relative()

        return imagery_item

    def make_self_link_relative(self) -> None:
        """Make the self link relative"""
        # FIXME: Should not need to remove `self` link as `add_link` already does that
        # self.clear_links(RelType.SELF)
        self_link = Link(target=f"./{self.id}.json", rel=RelType.SELF, media_type=MediaType.GEOJSON)
        self_link.target = f"./{self.id}.json"
        self.add_link(self_link)

    def update_checksum_related_metadata(self, file_content_checksum: str, stac_processing_data: STACProcessing) -> None:
        """Set the assets.visual.file:checksum attribute if it has changed.
        If the checksum has changed, this also updates the following attributes:
            assets.visual.updated
            properties.updated
            properties.processing:datetime
            properties.processing:software
            properties.processing:version

        Args:
            file_content_checksum (str): the new checksum
            stac_processing_data (STACProcessing): new data for the STAC processing extension attributes for this asset/item
        """
        visual_asset = self.assets["visual"]
        if file_content_checksum != visual_asset.extra_fields.get("file:checksum"):
            visual_asset.extra_fields["file:checksum"] = file_content_checksum
            visual_asset.extra_fields["updated"] = stac_processing_data["processing:datetime"]
            self.properties.update(stac_processing_data)
            self.properties["updated"] = stac_processing_data["processing:datetime"]

    def update_datetime(self, start_datetime: str, end_datetime: str) -> None:
        """Update the Item `start_datetime` and `end_datetime` property.

        Args:
            start_datetime: a start date in `YYYY-MM-DD` format
            end_datetime: a end date in `YYYY-MM-DD` format
        """
        self.properties["start_datetime"] = start_datetime
        self.properties["end_datetime"] = end_datetime
        self.properties["datetime"] = None

    # FIXME: why pystac uses list instead of tuple for bbox?
    def update_spatial(self, geometry: dict[str, Any], bbox: tuple[float, ...]) -> None:
        """Update the `geometry` and `bbox` (bounding box) of the Item.
        Args:
            geometry: a geometry
            bbox: a bounding box
        """
        self.geometry = geometry
        self.bbox = bbox

    def add_link(self, link: Link) -> None:
        if self.links and link.rel in [
            RelType.COLLECTION,
            RelType.PARENT,
            RelType.SELF,
        ]:  # STAC specification prescribes there can be only one of these
            self.links[:] = [l for l in self.links if l.rel != link.rel]

        super().add_link(link)

    # FIXME: how to refactor to use `set_collection` that needs a Collection object???
    def add_collection(self, collection_id: str) -> None:
        """Link a Collection to the Item as its `collection` and `parent`.

        Args:
            collection_id: the id of the collection to link
        """
        self.collection_id = collection_id
        self.add_link(Link(target="./collection.json", rel=RelType.COLLECTION, media_type=MediaType.JSON))
        self.add_link(Link(target="./collection.json", rel=RelType.PARENT, media_type=MediaType.JSON))

    # FIXME: why item can be a str?
    @typing.no_type_check
    def add_derived_from(self, *items: Item | str) -> Item:
        for item in items:
            file_content = json.dumps(item.to_dict()).encode("UTF-8")
            self.add_link(create_link_with_checksum(item.get_self_href(), RelType.DERIVED_FROM, MediaType.JSON, file_content))
        return self
