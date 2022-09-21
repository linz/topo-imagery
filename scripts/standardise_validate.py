from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, parse_multiple_arguments
from scripts.create_stac_items import create_imagery_items
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    concurrency: int = 1

    arguments = parse_multiple_arguments()

    source = format_source(arguments.source)

    if is_argo():
        concurrency = 4

    standardised_files = start_standardising(source, arguments.preset, concurrency)
    if standardised_files:
        non_visual_qa(standardised_files)
        create_imagery_items(
            standardised_files,
            format_date(arguments.start_datetime),
            format_date(arguments.end_datetime),
            arguments.collection,
        )
    else:
        get_log().info(
            "Non Visual QA skipped because no file has been standardised", action="standardise_validate", reason="skip"
        )


if __name__ == "__main__":
    main()
