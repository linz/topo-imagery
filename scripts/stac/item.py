from typing import Any, Dict

from linz_logger import get_log
from pystac import get_stac_version

from scripts.stac.util.checksum import multihash_as_hex
from scripts.stac.util.geotiff import get_extents
from scripts.stac.util.stac_extensions import StacExtensions


class ImageryItem:
    name = "item.imagery"
    id: str
    stac: Dict[str, Any]

    def __init__(self, item_id: str):
        self.id = item_id

    def create_stac_item(self, path: str, date: str) -> None:
        geometry, bbox = get_extents(path)
        self.stac = {
            "type": "Feature",
            "stac_version": get_stac_version(),
            "id": self.id,
            "properties": {
                "datetime": date,
            },
            "geometry": {"type": "Polygon", "coordinates": [geometry]},
            "bbox": bbox,
            "links": [
                {"rel": "self", "href": f"./{self.id}.json", "type": "application/json"},
            ],
            "assets": {"image": {"href": path, "type": "image/vnd.stac.geotiff", "file:checksum": multihash_as_hex(path)}},
            "stac_extensions": [StacExtensions.file.value],
        }
        get_log().info("imagery_stac_item_created", stac=self.stac, path=path)

    def validate_stac_item(self) -> bool:
        # TODO: will implement in future PR
        return True
