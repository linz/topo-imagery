from scripts.cli.cli_helper import parse_source
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import standardising


def main() -> None:
    source = parse_source()
    standardised_files = standardising(source)
    non_visual_qa(standardised_files)


if __name__ == "__main__":
    main()
