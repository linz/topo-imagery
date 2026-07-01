from datetime import datetime, timedelta, timezone
from random import choice, randint
from string import ascii_lowercase

from topo_imagery_common.datetimes import format_rfc_3339_datetime_string


def fake_linz_slug() -> str:
    random_string = "".join(choice(ascii_lowercase) for _ in range(6))
    start_year = randint(2000, 2009)
    end_year = randint(2010, 2019)
    gsd = choice([0.75, 0.3, 1, 0.075])

    return f"a-random-slug-{random_string}_{start_year}-{end_year}_{gsd}m"


def any_epoch_datetime() -> datetime:
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    return any_datetime_between(start, end)


def any_datetime_between(start: datetime, end: datetime) -> datetime:
    range_in_seconds = (end - start).total_seconds()
    return start + timedelta(seconds=randint(0, int(range_in_seconds)))


def any_epoch_datetime_string() -> str:
    return format_rfc_3339_datetime_string(any_epoch_datetime())
