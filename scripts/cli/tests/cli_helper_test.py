from typing import List

from scripts.cli.cli_helper import TileFiles, coalesce_multi_single, format_source, parse_list


def test_format_source_single_input() -> None:
    """example: --source s3://test/image_one.tiff"""
    source = ["s3://test/image_one.tiff"]
    tile_files: List[TileFiles] = format_source(source)
    input_files = tile_files[0].input
    assert len(input_files) == 1
    assert input_files == ["s3://test/image_one.tiff"]


def test_format_source_multiple_inputs() -> None:
    """example: --source s3://test/image_one.tiff s3://test/image_two.tiff"""
    source = ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]
    tile_files: List[TileFiles] = format_source(source)
    input_files = tile_files[0].input
    assert len(input_files) == 1
    assert input_files == ["s3://test/image_one.tiff"]
    assert tile_files[0].output == "image_one"
    input_files = tile_files[1].input
    assert len(input_files) == 1
    assert input_files == ["s3://test/image_two.tiff"]
    assert tile_files[1].output == "image_two"


def test_format_source_json_loading_error() -> None:
    """example: --source [s3://test/image_one.tiff"""
    source = ["[s3://test/image_one.tiff"]
    tile_files: List[TileFiles] = format_source(source)
    input_files = tile_files[0].input
    assert input_files == ["[s3://test/image_one.tiff"]


def test_parse_list() -> None:
    str_list = "Auckland Council; Toitū Te Whenua Land Information New Zealand;Nelson Council;"
    list_parsed = parse_list(str_list)
    assert list_parsed == ["Auckland Council", "Toitū Te Whenua Land Information New Zealand", "Nelson Council"]


def test_parse_list_empty() -> None:
    list_parsed = parse_list("")
    assert list_parsed == []


def test_format_source_tiles() -> None:
    input_source = [
        """[{"output": "tile_name","input": ["file_a.tiff", "file_b.tiff"]}, 
        {"output": "tile_name2","input": ["file_a.tiff", "file_b.tiff"]}]"""
    ]
    expected_output_filename = "tile_name"
    expected_output_filename_b = "tile_name2"
    expected_input_filenames = ["file_a.tiff", "file_b.tiff"]

    source: List[TileFiles] = format_source(input_source)
    assert expected_output_filename == source[0].output
    assert expected_input_filenames == source[0].input
    assert expected_output_filename_b == source[1].output


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
