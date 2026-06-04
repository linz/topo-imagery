from pytest_subtests import SubTests

from topo_imagery_common.files.files_helper import is_tiff


def test_is_tiff(subtests: SubTests) -> None:
    file_a = "file.tiff"
    file_b = "file.tif"
    file_c = "file.TIFF"
    file_d = "file.jpg"

    with subtests.test():
        assert is_tiff(file_a) is True

    with subtests.test():
        assert is_tiff(file_b) is True

    with subtests.test():
        assert is_tiff(file_c) is True

    with subtests.test():
        assert is_tiff(file_d) is False
