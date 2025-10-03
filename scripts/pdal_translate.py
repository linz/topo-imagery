import argparse
import filecmp
import json
import os
import tempfile
from functools import partial
from multiprocessing import Pool
from typing import Any, Iterable

from linz_logger import get_log

from scripts.cli.cli_helper import is_argo
from scripts.files.files_helper import ContentType
from scripts.files.fs import copy, exists, read, write
from scripts.logging.time_helper import time_in_ms
from scripts.pdal.pdal_commands import pdal_translate_add_proj_command, run_pdal


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        dest="force",
        help="Overwrite existing files even if they did not change. Defaults to False.",
        action="store_true",
    )
    parser.add_argument(
        "--from-file",
        dest="from_file",
        type=json_file_loader,
        required=False,
        help="JSON file containing a nested list of files to process. "
        "If provided, this will be processed in addition to other file arguments.",
    )
    parser.add_argument(
        "--from-manifest",
        dest="from_manifest",
        type=manifest_loader,
        required=False,
        help="JSON file containing a manifest of files to process. "
        "If provided, this will be processed in addition to other file arguments.",
    )
    parser.add_argument(
        "--files",
        dest="files",
        type=non_empty_str,
        nargs="+",
        required=False,
        help="List of files to process (space separated). "
        "If provided, this will be processed in addition to other file arguments.",
    )
    parser.add_argument(
        "--target",
        dest="target",
        required=False,
        default="/tmp/",
        help="Path where the output files will be saved to. Defaults to '/tmp/'.",
    )

    return parser


def flatten(items: list[Any]) -> Iterable[Any]:
    """Recursively flatten a nested list into a flat sequence.

    Args:
        items: a potentially nested list

    Returns:
        Any: The flattened elements, one by one
    """
    for item in items:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


def non_empty_str(s: str) -> list[str]:
    """Check if a string is non-empty after stripping whitespace.

    Args:
        s: input string
    Returns:
        The original string as a list if non-empty, or an empty list otherwise.
    """
    if not s or s.strip() == "":
        return []
    return [s]


def json_file_loader(path: str) -> list[str]:
    """Load a JSON file and return its contents as a list of strings.

    Args: path: path to the JSON file
    Returns:
        A list of strings contained in the JSON file.
    """
    if not path:
        return []
    try:
        return list(flatten(json.loads(read(path))))
    except FileNotFoundError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        return []


def manifest_loader(path: str) -> list[str]:
    """Load a JSON manifest file (compatible with our create-manifest workflow) and return its sources as a list of strings.

    Args: path: path to the manifest file
    Returns:
        A list of strings contained in the manifest.
    """
    if not path:
        return []
    try:
        manifest = json.loads(read(path))
        return list(flatten([entry["source"] for entry in manifest.get("parameters", {}).get("manifest", [])]))
    except FileNotFoundError as e:
        get_log().error("An error occurred when loading the input file.", error=str(e))
        return []


def pdal_translate(
    source_file: str,
    target: str = "/tmp/",
    force: bool = False,
) -> str | None:
    """Fix LAZ files by adding consistent CRS information in the header.

    Args:
        source_file: /path/to/a/file to process (S3 or local).
        target: path where the output files need to be saved to. Defaults to "/tmp/".
        force: overwrite existing output file even if it did not change. Defaults to False.

    Returns:
        The name of the fixed LAZ file if it is different to the input file, else None.
    """
    basename = source_file.split("/")[-1]
    target_file = os.path.join(target, basename)

    # Already processed can skip processing
    if exists(target_file):
        if not force:
            get_log().info("Skipping: Output file already exists.", path=target_file)
            # Note: Some of these may be unchanged from the input file. Err on side of caution and return the basename.
            return target_file
        get_log().info("Overwriting: Output file already exists.", path=target_file)

    with tempfile.TemporaryDirectory() as tmp_path:  # pdal needs local files
        tmp_file_in = os.path.join(tmp_path, "in_" + basename)
        tmp_file_out = os.path.join(tmp_path, "out_" + basename)

        copy(source=source_file, target=tmp_file_in)

        run_pdal(pdal_translate_add_proj_command, input_file=tmp_file_in, output_file=tmp_file_out)

        copy(source=tmp_file_out, target=target_file)  # copy back to target location (S3 or local) before comparing

        if not force and filecmp.cmp(tmp_file_in, tmp_file_out, shallow=False):
            get_log().info("No changes made to file.", path=source_file)
            return None

        return target_file


def run_pdal_translate(
    files_to_process: list[str],
    concurrency: int,
    target: str = "/tmp/",
    force: bool = False,
) -> list[str]:
    """Run `pdal_translate()` in parallel (see `concurrency`).

    Args:
        files_to_process: list of files to process
        concurrency: number of concurrent tiles to process
        target: output directory path. Defaults to "/tmp/"
        force: overwrite existing files. Defaults to False.

    Returns:
        the list of generated hillshade TIFF paths with their input files.
    """
    with Pool(concurrency) as p:
        results = list(p.map(partial(pdal_translate, target=target, force=force), files_to_process))
        p.close()
        p.join()

    return [result for result in results if result is not None]


def main() -> None:
    start_time = time_in_ms()
    arguments_parser = get_args_parser()
    arguments = arguments_parser.parse_args()

    input_files: list[str] = []
    for arg in [arguments.files, arguments.from_file, arguments.from_manifest]:
        if arg:
            input_files.extend(arg)

    input_files = list(flatten(input_files))

    if len(input_files) == 0:
        get_log().info("no_files_to_process", action="pdal_translate", reason="skipped")
        return

    pdal_version = os.environ.get("PDAL_VERSION", "unknown_pdal_version")

    get_log().info("pdal_translate_start", pdalVersion=pdal_version, inputFileCount=len(input_files))

    concurrency: int = 1
    if is_argo():
        concurrency = 4

    output_files = run_pdal_translate(input_files, concurrency, force=arguments.force, target=arguments.target)
    modified_file_count = len(output_files)
    write("/tmp/modified_file_count", bytes(f"{modified_file_count}", "UTF-8"))
    if modified_file_count > 0:
        write("/tmp/processed.json", bytes(json.dumps(output_files), "UTF-8"), content_type=ContentType.JSON)

    get_log().info("pdal_translate_end", duration=time_in_ms() - start_time, modifiedFileCount=modified_file_count)


if __name__ == "__main__":
    main()
