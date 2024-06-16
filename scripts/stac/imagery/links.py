from pystac import Link

CHECKSUM_PROPERTY_NAME = "file:checksum"


class ComparableLink(Link):
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Link):
            return NotImplemented

        return self.to_dict() == other.to_dict()
