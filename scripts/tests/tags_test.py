from scripts.standardising import tag_sets


def test_get_tags() -> None:
    assert next(tag_sets("scripts/tests/data/empty.tiff"))["TileByteCounts"].value == (0,)
