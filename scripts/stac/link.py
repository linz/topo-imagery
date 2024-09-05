from enum import Enum

from scripts.stac.util import checksum
from scripts.stac.util.media_type import StacMediaType


class Relation(str, Enum):
    """https://github.com/radiantearth/stac-spec/blob/master/commons/links.md#hierarchical-relations"""

    SELF = "self"
    ROOT = "root"
    PARENT = "parent"
    COLLECTION = "collection"
    ITEM = "item"
    DERIVED_FROM = "derived_from"
    """ https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#derived-from-relation-derived_from"""


# pylint: disable=too-few-public-methods
class Link:
    """Represents a STAC Link Object (https://github.com/radiantearth/stac-spec/blob/master/commons/links.md#link-object).

    Attributes:
        path: A string that represents the actual link in the format of an URL.
        rel: A string that represents the relationship that the link has to the object it will be added to.
        media_type: `StacMediaType` of the link file.
        file_content: Optional. The content of the file that will be used to store the checksum in `file:checksum`.
        It assumes using the STAC `file` extension.
    """

    stac: dict[str, str]

    def __init__(self, path: str, rel: str, media_type: StacMediaType, file_content: bytes | None = None) -> None:
        self.stac = {
            "href": path,
            "rel": rel,
            "type": media_type,
        }

        if file_content:
            self.stac["file:checksum"] = checksum.multihash_as_hex(file_content)
