from datetime import datetime

from pytest import raises
from pytest_subtests import SubTests

from scripts.cli.cli_helper import TileFiles, coalesce_multi_single, get_tile_files, parse_list, valid_date


def test_get_tile_files(subtests: SubTests) -> None:
    file_source = '[{"output": "tile_name","input": ["file_a.tiff", "file_b.tiff"]}, \
    {"output": "tile_name2","input": ["file_a.tiff", "file_b.tiff"]}]'
    expected_output_filename = "tile_name"
    expected_output_filename_b = "tile_name2"
    expected_input_filenames = ["file_a.tiff", "file_b.tiff"]

    source: list[TileFiles] = get_tile_files(file_source)
    with subtests.test():
        assert expected_output_filename == source[0].output

    with subtests.test():
        assert expected_input_filenames == source[0].inputs

    with subtests.test(msg="Should not include derived by default"):
        assert source[0].includeDerived is False

    with subtests.test():
        assert expected_output_filename_b == source[1].output


def test_get_tile_files_with_include_derived(subtests: SubTests) -> None:
    file_source = '[{"output": "tile_name","input": ["file_a.tiff", "file_b.tiff"], "includeDerived": true}]'
    expected_output_filename = "tile_name"
    expected_input_filenames = ["file_a.tiff", "file_b.tiff"]

    source: list[TileFiles] = get_tile_files(file_source)
    with subtests.test():
        assert expected_output_filename == source[0].output

    with subtests.test():
        assert expected_input_filenames == source[0].inputs

    with subtests.test():
        assert source[0].includeDerived is True


def test_parse_list() -> None:
    str_list = "Auckland Council; Toitū Te Whenua Land Information New Zealand;Nelson Council;"
    list_parsed = parse_list(str_list)
    assert list_parsed == ["Auckland Council", "Toitū Te Whenua Land Information New Zealand", "Nelson Council"]


def test_parse_list_empty() -> None:
    list_parsed = parse_list("")
    assert list_parsed == []


def test_coalesce_multi_no_single() -> None:
    multi_items = "foo; bar baz"
    single_item = ""
    coalesced_list = coalesce_multi_single(multi_items, single_item)
    assert coalesced_list == ["foo", "bar baz"]


def test_coalesce_single_no_multi() -> None:
    multi_items = ""
    single_item = "foo"
    coalesced_list = coalesce_multi_single(multi_items, single_item)
    assert coalesced_list == ["foo"]


def test_coalesce_nothing() -> None:
    # pylint: disable-msg=use-implicit-booleaness-not-comparison
    multi_items = ""
    single_item = ""
    coalesced_list = coalesce_multi_single(multi_items, single_item)
    assert coalesced_list == []


def test_valid_date_empty_string() -> None:
    assert valid_date("") is None


def test_valid_date_valid_string() -> None:
    assert isinstance(valid_date("2024-11-21"), datetime)


def test_valid_date_invalid_string() -> None:
    with raises(Exception) as e:
        valid_date("foo")
        assert str(e.value) == "not a valid date: foo"
