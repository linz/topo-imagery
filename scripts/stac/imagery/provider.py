from enum import Enum
from typing import TypedDict


class ProviderRole(str, Enum):
    PRODUCER = "producer"
    LICENSOR = "licensor"
    PROCESSOR = "processor"
    HOST = "host"


class Provider(TypedDict):
    name: str
    """Organization name"""
    roles: list[ProviderRole]
    """Organization roles"""


def merge_provider_roles(providers: list[Provider]) -> list[Provider]:
    """Merge the roles of the providers with the same name.
    Does not manage duplicates in the final roles list.

    Args:
        providers: a list of `Provider` objects

    Returns:
        a list of `Provider` objects with merged roles

    Example:
        >>> merge_provider_roles([{"name": "Maxar", "roles": [ProviderRole.PRODUCER]}, {"name": "Maxar",\
              "roles": [ProviderRole.LICENSOR]}])
        [{'name': 'Maxar', 'roles': [<ProviderRole.PRODUCER: 'producer'>, <ProviderRole.LICENSOR: 'licensor'>]}]
    """
    merged_providers: list[Provider] = []
    for provider in providers:
        if provider["name"] not in [p["name"] for p in merged_providers]:
            merged_providers.append(provider)
        else:
            for p in merged_providers:
                if p["name"] == provider["name"]:
                    p["roles"].extend(provider["roles"])
    return merged_providers
