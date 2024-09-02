from enum import Enum


class StacMediaType(str, Enum):
    """ https://github.com/radiantearth/stac-spec/blob/master/commons/links.md#stac-media-types """
    JSON = "application/json"
    """ For STAC Catalog and Collection """
    GEOJSON = "application/geo+json"
    """ https://www.iana.org/assignments/media-types/application/geo+json
        
        For STAC Item 
    """
