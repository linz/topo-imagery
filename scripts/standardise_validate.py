import argparse

from linz_logger import get_log

from scripts.cli.cli_helper import format_date, format_source, is_argo, valid_date
from scripts.create_stac_items import create_imagery_items
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    concurrency: int = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", dest="preset", required=True)
    parser.add_argument("--source", dest="source", nargs="+", required=True)
    parser.add_argument(
        "--start_datetime", dest="start_datetime", help="start datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "--end_datetime", dest="end_datetime", help="end datetime in format YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument("--collection", dest="collection", help="path to collection.json", required=True)

    arguments = parser.parse_args()

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
