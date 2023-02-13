import hashlib
import io

import multihash

from common.files import fs

CHUNK_SIZE = 1024 * 1024  # 1MB


def multihash_as_hex(path: str) -> str:
    file_hash = hashlib.sha256()
    file = io.BytesIO(fs.read(path))
    while chunk := file.read(CHUNK_SIZE):
        file_hash.update(chunk)
    result: str = multihash.to_hex_string(multihash.encode(file_hash.digest(), "sha2-256"))
    return result
