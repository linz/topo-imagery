from typing import Any, Dict, List

from pystac import get_stac_version

from scripts.files.files_helper import get_file_name_from_path, strip_extension
from scripts.stac.util import checksum  # dont touch this
from scripts.stac.util.stac_extensions import StacExtensions


class ImageryItem:
    id: str
    path: str
    datetime: str
    geometry: List[List[float]]
    bbox: List[float]
    checksum: str
    stac: Dict[str, Any]

    def __init__(self, path: str, datetime: str, geometry: List[List[float]], bbox: List[float]) -> None:
        self.path = path
        self.datetime = datetime
        self.geometry = geometry
        self.bbox = bbox
        self.id = strip_extension(get_file_name_from_path(path))
        self.checksum = checksum.multihash_as_hex(path)

    def create_core_stac(self) -> None:
        self.stac = {
            "type": "Feature",
            "stac_version": get_stac_version(),
            "id": self.id,
            "properties": {
                "datetime": self.datetime,
            },
            "geometry": {"type": "Polygon", "coordinates": [self.geometry]},
            "bbox": self.bbox,
            "links": [
                {"rel": "self", "href": f"./{self.id}.json", "type": "application/json"},
            ],
            "assets": {
                "image": {
                    "href": self.path,
                    "type": "image/tiff; application:geotiff; profile:cloud-optimized",
                    "file:checksum": self.checksum,
                }
            },
            "stac_extensions": [StacExtensions.file.value],
        }

    def validate_stac(self) -> bool:
        # TODO: will implement in future PR
        return True

# class ImageryCollection:
#     items = List[ImageryItem]

#     def __init__(self) -> None:
#         # TODO: will implement in future PR
#         pass

#     def create_stac(self) -> None:
#         # TODO: will implement in future PR
#         pass

#     def validate_collection(self) -> bool:
#         # TODO: will implement in future PR
#         return True
