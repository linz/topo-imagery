import argparse
from typing import Any


class CommonArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_argument(
            "--is-argo",
            dest="is_argo",
            help="Specify if the process is running in an Argo Workflows (for concurrency optimisation).",
            action="store_true",
        )
