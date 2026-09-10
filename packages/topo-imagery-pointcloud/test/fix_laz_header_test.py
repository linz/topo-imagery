import json
from pathlib import Path
from unittest.mock import patch

from topo_imagery_pointcloud.fix_laz_header import (
    flatten,
    json_file_loader,
    manifest_loader,
    non_empty_str,
    pdal_fix_laz_header,
)


def test_flatten_returns_a_flat_list_unchanged() -> None:
    assert list(flatten(["a", "b"])) == ["a", "b"]


def test_flatten_flattens_nesting_at_any_depth() -> None:
    """`--from-file` accepts a nested list, which is what the workflows that generate it produce."""
    assert list(flatten([["a"], ["b", ["c", ["d"]]]])) == ["a", "b", "c", "d"]


def test_flatten_returns_nothing_for_an_empty_list() -> None:
    assert not list(flatten([]))


def test_non_empty_str_wraps_a_value_in_a_list() -> None:
    assert non_empty_str("a/file.laz") == ["a/file.laz"]


def test_non_empty_str_discards_blank_values() -> None:
    """Argo passes an empty string for an unset parameter, which must not become a file to process."""
    for blank in ["", " ", "\t\n"]:
        assert not non_empty_str(blank)


def test_json_file_loader_flattens_the_file_it_reads(tmp_path: Path) -> None:
    from_file = tmp_path / "files.json"
    from_file.write_text(json.dumps([["a.laz"], ["b.laz", "c.laz"]]))

    assert json_file_loader(str(from_file)) == ["a.laz", "b.laz", "c.laz"]


def test_json_file_loader_returns_nothing_for_a_missing_file(tmp_path: Path) -> None:
    """Regression: `read()` raises `NoSuchFileError`, not `FileNotFoundError`."""
    assert not json_file_loader(str(tmp_path / "absent.json"))


def test_json_file_loader_returns_nothing_for_an_empty_path() -> None:
    assert not json_file_loader("")


def test_manifest_loader_returns_the_sources(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"parameters": {"manifest": [{"source": "a.laz", "target": "x"}, {"source": "b.laz", "target": "y"}]}})
    )

    assert manifest_loader(str(manifest)) == ["a.laz", "b.laz"]


def test_manifest_loader_returns_nothing_for_a_manifest_without_entries(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"parameters": {}}))

    assert not manifest_loader(str(manifest))


def test_manifest_loader_returns_nothing_for_a_missing_file(tmp_path: Path) -> None:
    """Regression: `read()` raises `NoSuchFileError`, not `FileNotFoundError`."""
    assert not manifest_loader(str(tmp_path / "absent.json"))


def test_pdal_fix_laz_header_skips_a_file_that_has_already_been_processed(tmp_path: Path) -> None:
    """An existing output is returned without running pdal, because it may differ from its input."""
    target_file = tmp_path / "a.laz"
    target_file.write_bytes(b"already processed")

    with patch("topo_imagery_pointcloud.fix_laz_header.run_pdal") as run_pdal:
        result = pdal_fix_laz_header("s3://bucket/a.laz", target=str(tmp_path))

    assert result == str(target_file)
    run_pdal.assert_not_called()
