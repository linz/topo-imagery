from linz_logger import get_log

from scripts.cli.cli_helper import is_argo, parse_source
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    concurrency: int = 1
    source = parse_source()
    if is_argo():
        concurrency = 4
    standardised_files = start_standardising(source, "lzw", concurrency)
    if standardised_files:
        non_visual_qa(standardised_files)
    else:
        get_log().info(
            "Non Visual QA skipped because no file has been standardised", action="standardise_validate", reason="skip"
        )


if __name__ == "__main__":
    main()
