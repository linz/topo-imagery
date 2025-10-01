import argparse
import filecmp
import json
import os
import sys
import tempfile
from functools import partial
from multiprocessing import Pool
from typing import Any, Iterable

from linz_logger import get_log

from scripts.cli.cli_helper import InputParameterError, is_argo
from scripts.files.files_helper import ContentType
from scripts.files.fs import copy, exists, read, write
from scripts.logging.time_helper import time_in_ms
from scripts.pdal.pdal_commands import pdal_translate_add_proj_command, run_pdal


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file",
        dest="from_file",
        required=False,
        help="JSON file containing a nested list of files to process. If provided, this will be added to --files.",
    )
    parser.add_argument(
        "--force",
        dest="force",
        help="Overwrite existing files even if they did not change. Defaults to False.",
        action="store_true",
    )
    parser.add_argument(
        "--files",
        dest="files",
        nargs="+",
        required=False,
        help="List of files to process (space separated). If provided, this will be processed in addition to --from-file.",
    )

    return parser


def flatten(items: list[Any]) -> Iterable[Any]:
    """Recursively flatten a nested list into a flat sequence.

    Args:
        items: a potentially nested list

    Returns:
        Any: The flattened elements, one by one
    """
    for x in items:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x


def pdal_translate(
    file: str,
    target_output: str = "/tmp/",
    force: bool = False,
) -> str | None:
    """Fix LAZ files by adding consistent CRS information in the header.

    Args:
        file: /path/to/a/file to process (S3 or local).
        target_output: path where the output files need to be saved to. Defaults to "/tmp/".
        force: overwrite existing output file even if it did not change. Defaults to False.

    Returns:
        The filename of the fixed LAZ file if it is different to the input file, else None.
    """
    filename = file.split("/")[-1]
    output_full_path = os.path.join(target_output, filename)

    # Already processed can skip processing
    if exists(output_full_path):
        if not force:
            get_log().info("Skipping: Output file already exists.", path=output_full_path)
            # Note: Some of these may be unchanged from the input file. Err on side of caution and return the filename.
            return output_full_path
        get_log().info("Overwriting: Output file already exists.", path=output_full_path)

    # Download any needed file from S3 ["/foo/bar.tiff", "s3://foo"] => "/tmp/bar.tiff", "/tmp/foo.tiff"
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_file_in = os.path.join(tmp_path, filename)
        tmp_file_out = os.path.join(tmp_path, "out_" + filename)
        source_file = copy(source=file, target=tmp_file_in)

        # Get PDAL to write to temporary location so no broken files end up in the final folder.
        run_pdal(pdal_translate_add_proj_command, input_file=source_file, output_file=tmp_file_out)

        write(output_full_path, read(tmp_file_out), content_type=ContentType.LAZ)

        if filecmp.cmp(tmp_file_out, output_full_path, shallow=False):
            get_log().info("No changes made to file.", path=output_full_path)
            return None

        return output_full_path


def run_pdal_translate(
    files_to_process: list[str],
    concurrency: int,
    target_output: str = "/tmp/",
    force: bool = False,
) -> list[str]:
    """Run `pdal_translate()` in parallel (see `concurrency`).

    Args:
        files_to_process: list of files to process
        concurrency: number of concurrent tiles to process
        target_output: output directory path. Defaults to "/tmp/"
        force: overwrite existing files. Defaults to False.

    Returns:
        the list of generated hillshade TIFF paths with their input files.
    """
    with Pool(concurrency) as p:
        results = list(p.map(partial(pdal_translate, target_output=target_output, force=force), files_to_process))
        p.close()
        p.join()

    return [result for result in results if result is not None]


def main() -> None:
    start_time = time_in_ms()
    arguments_parser = get_args_parser()
    arguments = arguments_parser.parse_args()

    input_files: list[str] = []
    if arguments.files:
        input_files.append(arguments.files)
    try:
        if arguments.from_file:
            with open(arguments.from_file, "r", encoding="utf-8") as f:
                input_files.extend(json.load(f))
    except InputParameterError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        sys.exit(1)

    if len(input_files) == 0:
        get_log().info("no_files_to_process", action="pdal_translate", reason="skipped")
        return

    pdal_version = os.environ.get("PDAL_VERSION", "unknown_pdal_version")
    input_files = [item for sub in input_files for item in (sub if isinstance(sub, list) else [sub])]
    get_log().info("pdal_translate_start", pdalVersion=pdal_version, inputFileCount=len(input_files))

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    output_files = run_pdal_translate(input_files, concurrency, force=arguments.force)
    write("/tmp/processed.json", bytes(json.dumps(output_files), "UTF-8"), content_type=ContentType.JSON)

    get_log().info("pdal_translate_end", duration=time_in_ms() - start_time, modifiedFileCount=len(output_files))


if __name__ == "__main__":
    main()
