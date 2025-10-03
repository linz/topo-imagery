import tempfile
from shutil import rmtree

from scripts.pdal_translate import run_pdal_translate


def test_return_list_of_all_files_if_force() -> None:
    source = ["scripts/tests/data/pdal_bad_header_1.laz", "scripts/tests/data/pdal_good_header_1.laz"]
    target = tempfile.mkdtemp()

    processed = run_pdal_translate(source, concurrency=1, target=target, force=True)
    rmtree(target)

    assert processed == [f"{target}/pdal_bad_header_1.laz", f"{target}/pdal_good_header_1.laz"]


def test_return_list_of_changed_files() -> None:
    source = ["scripts/tests/data/pdal_bad_header_1.laz", "scripts/tests/data/pdal_good_header_1.laz"]
    target = tempfile.mkdtemp()

    processed = run_pdal_translate(source, concurrency=1, target=target, force=False)
    rmtree(target)

    assert processed == [f"{target}/pdal_bad_header_1.laz"]
