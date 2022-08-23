from scripts.cli.cli_helper import is_argo, parse_source
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    concurrency: int = 1
    source = parse_source()
    if is_argo():
        concurrency = 4
    standardised_files = start_standardising(source, concurrency)
    non_visual_qa(standardised_files)


if __name__ == "__main__":
    main()
