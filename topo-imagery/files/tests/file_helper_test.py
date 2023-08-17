from topo-imagery.files.files_helper import is_tiff


def test_is_tiff() -> None:
    file_a = "file.tiff"
    file_b = "file.tif"
    file_c = "file.TIFF"
    file_d = "file.jpg"

    assert is_tiff(file_a) is True
    assert is_tiff(file_b) is True
    assert is_tiff(file_c) is True
    assert is_tiff(file_d) is False
