from enum import Enum
from typing import Optional

import xmltodict
from linz_logger import get_log


class MetadataType(str, Enum):
    EARTHSCANNER = "earthscanner"


def get_cloud_percent(xml_input: str) -> Optional[int]:
    try:
        input_metadata = xmltodict.parse(xml_input)
        cloud_percent: int = int(input_metadata["MetaData"]["ProductInfo"]["CloudPercent"])
    except Exception as e:
        get_log().error("Bad XML metadata format", error=e)
        return None
    return cloud_percent
