from pystac import Asset, MediaType


def create_visual_asset(href: str, created: str, checksum: str, updated: str | None = None) -> Asset:
    """Create a visual Asset"""
    if not updated:
        updated = created
    extra_fields = {"created": created, "updated": updated}
    if checksum:
        extra_fields["file:checksum"] = checksum
    return Asset(href=href, title="visual", media_type=MediaType.COG, extra_fields=extra_fields)
