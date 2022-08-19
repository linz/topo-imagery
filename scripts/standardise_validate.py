from scripts.aws.aws_helper import is_argo
from scripts.cli.cli_helper import parse_source
from scripts.non_visual_qa import non_visual_qa
from scripts.standardising import start_standardising


def main() -> None:
    source = parse_source()
    argo_env = is_argo()
    standardised_files = start_standardising(source, argo_env)
    non_visual_qa(standardised_files)


if __name__ == "__main__":
    main()
