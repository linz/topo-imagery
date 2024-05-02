import json
from typing import Any, Dict


def dict_to_json_bytes(input_dict: Dict[str, Any], ensure_ascii: bool = True) -> bytes:
    return json.dumps(input_dict, ensure_ascii=ensure_ascii).encode("utf-8")
