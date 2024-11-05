from datetime import datetime
from typing import Callable


def fixed_now_function(now: datetime) -> Callable[[], datetime]:
    def func() -> datetime:
        return now

    return func
