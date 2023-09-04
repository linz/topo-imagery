import argparse
import json
import os
import tempfile

from scripts.files.fs import find_sidecars, read, write_all
from scripts.gdal.gdal_helper import run_gdal
from scripts.gdal.gdal_preset import get_ascii_translate_command


def main() -> None:
    """Translates ascii files in a given path to tiffs and writes to target,

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

    asc_files = json.loads(read(arguments.from_file))

    with tempfile.TemporaryDirectory() as tmp_path:
        tiffs = []
        for ls in asc_files:
            for asc in ls:
                # translate from ascii to geotiff using GDAL
                filename = os.path.splitext(os.path.basename(asc))[0]
                tiff = os.path.join(tmp_path, f"{filename}.tiff")
                run_gdal(get_ascii_translate_command(), input_file=asc, output_file=tiff)
                tiffs.append(tiff)
        write_all(inputs=tiffs, target=arguments.target)

        # copy any sidecar files to target
        sidecars = []
        for ls in asc_files:
            sidecars += find_sidecars(ls, [".prj", ".tfw"])
        write_all(inputs=sidecars, target=arguments.target)


if __name__ == "__main__":
    main()
