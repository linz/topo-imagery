from source_formatter import format_source_from_basemaps_cli


def test_format_source_from_basemaps_cli_file() -> None:
    """Based on output from basemaps cli
    example: --source "[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"    
    """
    source = ["[\"s3://test/image_one.tiff\", \"s3://test/image_two.tiff\"]"]
    file_list = format_source_from_basemaps_cli(source[0])
    assert isinstance(file_list, list)
    assert len(file_list) == 2
    assert file_list[0] == "s3://test/image_one.tiff"
