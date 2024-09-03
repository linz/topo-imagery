from pathlib import Path

from scripts.stac.imagery.create_stac import create_item


def test_create_item_with_derived_from(tmp_path: Path) -> None:
    derived_from_path = tmp_path / "derived_from_item.json"
    derived_from_path.write_text('{"type": "Feature", "id": "fake_item"}')

    item = create_item(
        "./scripts/tests/data/empty.tiff", "2024-01-01", "2024-01-02", "abc123", derived_from=[f"{derived_from_path}"]
    )

    assert {
        "href": f"{derived_from_path}",
        "rel": "derived_from",
        "type": "application/json",
        "file:checksum": "12208010297a79dc2605d99cde3d1ca63f72647637529ef6eb3d57eef1c951dcf939",
    } in item.stac["links"]
