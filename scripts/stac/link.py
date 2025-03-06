from pystac import Link, MediaType, RelType

from scripts.stac.util import checksum


def create_link_with_checksum(path: str, rel: RelType, media_type: MediaType, file_content: bytes) -> Link:
    return Link(
        target=path,
        rel=rel,
        media_type=media_type,
        extra_fields={"file:checksum": checksum.multihash_as_hex(file_content)},
    )
