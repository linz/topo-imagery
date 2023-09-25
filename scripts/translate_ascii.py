import argparse
import json
import os
import tempfile
from functools import partial
from multiprocessing import Pool

from scripts.cli.cli_helper import is_argo
from scripts.files.files_helper import get_file_name_from_path
from scripts.files.fs import find_sidecars, read, write_all
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_ascii_translate_command


def main() -> None:
    """Translates ascii files in a given path to tiffs and writes to target along with their sidecar (`.prj`, `.tfw`) files.

    Arguments:
    --from-file - file listing the source data
    --target - local or s3 path to write converted tiffs

    examples:
        python translate_ascii.py --from-file s3://linz-elevation-staging/test/sample-tests/file-list.json --target /tmp/
        python translate_ascii.py --from-file ./tests/data/file-list.json --target /tmp/
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--from-file", dest="from_file", required=True, help="Path to file listing ascii files")
    parser.add_argument("--target", dest="target", required=True, help="Output location path")
    arguments = parser.parse_args()

    asc_files = json.loads(read(arguments.from_file))[0]

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    with tempfile.TemporaryDirectory() as tmp_path:
        with Pool(concurrency) as p:
            tiffs = p.map(
                partial(
                    translate_ascii,
                    target_dir_path=tmp_path,
                ),
                asc_files,
            )
        p.close()
        p.join()

        write_all(inputs=tiffs, target=arguments.target)

        # copy any sidecar files to target
        sidecars = []
        for ls in asc_files:
            sidecars += find_sidecars(ls, [".prj", ".tfw"])
        write_all(inputs=sidecars, target=arguments.target)

def translate_ascii(file: str, target_dir_path: str) -> str:
    """Translates from ascii to geotiff using GDAL
    Args:
        file: the local file path to translate
        target_dir_path: the directory path to write the translated file

    Returns:
        full path to translated file
    """
    filename = get_file_name_from_path(file)
    tiff = os.path.join(target_dir_path, f"{filename}.tiff")
    run_gdal(get_ascii_translate_command(), input_file=file, output_file=tiff)
    return tiff


if __name__ == "__main__":
    main()
