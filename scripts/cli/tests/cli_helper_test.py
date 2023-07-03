from scripts.cli.cli_helper import coalesce_multi_single, format_source, parse_list


def test_format_source_from_basemaps_cli_file() -> None:
    """Based on output from basemaps cli
    example: --source "[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"
    """
    # fmt: off
    source = ["[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"]
    # fmt: on
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 2
    assert file_list == ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]


def test_format_source_single_input() -> None:
    """example: --source s3://test/image_one.tiff"""
    source = ["s3://test/image_one.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 1
    assert file_list == ["s3://test/image_one.tiff"]


def test_format_source_multiple_inputs() -> None:
    """example: --source s3://test/image_one.tiff s3://test/image_two.tiff"""
    source = ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 2
    assert file_list == ["s3://test/image_one.tiff", "s3://test/image_two.tiff"]


def test_format_source_json_loading_error() -> None:
    """example: --source [s3://test/image_one.tiff"""
    source = ["[s3://test/image_one.tiff"]
    file_list = format_source(source)
    assert isinstance(file_list, list)
    assert len(file_list) == 1
    assert file_list == ["[s3://test/image_one.tiff"]


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
    assert isinstance(coalesced_list, list)
    assert coalesced_list == ["foo", "bar baz"]


def test_coalesce_single_no_multi() -> None:
    multi_items = ""
    single_item = "foo"
    coalesced_list = coalesce_multi_single(multi_items, single_item)
    assert isinstance(coalesced_list, list)
    assert coalesced_list == ["foo"]


def test_coalesce_nothing() -> None:
    multi_items = ""
    single_item = ""
    coalesced_list = coalesce_multi_single(multi_items, single_item)
    assert isinstance(coalesced_list, list)
    assert coalesced_list == []
