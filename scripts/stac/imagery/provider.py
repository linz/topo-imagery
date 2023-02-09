from enum import Enum
from typing import List, TypedDict


class ProviderRole(str, Enum):
    PRODUCER = "producer"
    LICENSOR = "licensor"
    PROCESSOR = "processor"
    HOST = "host"


class Provider(TypedDict):
    name: str
    """Organization name"""
    roles: List[ProviderRole]
    """Organization roles"""
