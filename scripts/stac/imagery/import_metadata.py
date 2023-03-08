from enum import Enum

import xmltodict
from linz_logger import get_log


class MetadataType(str, Enum):
    EARTHSCANNER = "earthscanner"


def get_cloud_percent(xml_input: str) -> str:
    try:
        input_metadata = xmltodict.parse(xml_input)
        cloud_percent: str = input_metadata["MetaData"]["ProductInfo"]["CloudPercent"]
    except Exception as e:  # pylint: disable-msg=broad-exception-caught
        get_log().error("Bad XML metadata format", error=e)
        return ""
    return cloud_percent
