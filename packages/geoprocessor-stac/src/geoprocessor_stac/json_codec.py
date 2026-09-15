import json
from typing import Any


def dict_to_json_bytes(input_dict: dict[str, Any]) -> bytes:
    """
    Try to convert a `dict` into UTF-8 encoded `bytes` representing a JSON dictionary

    Examples:
        >>> dict_to_json_bytes({})
        b'{}'
        >>> dict_to_json_bytes({"ā": "😀"}) # Unicode code points U+0101 and U+1F600
        b'{"\xc4\x81": "\xf0\x9f\x98\x80"}'
        >>> json.loads(dict_to_json_bytes({"ā": "😀"}))
        {'ā': '😀'}
    """
    return json.dumps(input_dict, ensure_ascii=False).encode("utf-8")
