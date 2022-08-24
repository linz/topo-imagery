from linz_logger import get_log

from scripts.cli.cli_helper import is_argo, parse_source
from scripts.logging.logging_keys import LOG_REASON_SKIP, LOG_REASON_SUCCESS
from scripts.logging.time_helper import time_in_ms
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    start_time = time_in_ms()
    action = "standardise_validate"
    concurrency: int = 1
    source = parse_source()
    if is_argo():
        concurrency = 4
    standardised_files = start_standardising(source, concurrency)
    if standardised_files:
        non_visual_qa(standardised_files)
        get_log().info(
            "Standardise and validate with Non Visual QA ended",
            action=action,
            reason=LOG_REASON_SUCCESS,
            source=source,
            duration=time_in_ms() - start_time,
        )
    else:
        get_log().info(
            "Non Visual QA skipped because no file has been standardised",
            action=action,
            source=source,
            reason=LOG_REASON_SKIP,
        )


if __name__ == "__main__":
    main()
