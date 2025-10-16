from datetime import datetime, timedelta, timezone
from random import randint

from scripts.datetimes import format_rfc_3339_datetime_string


def any_epoch_datetime() -> datetime:
    """
    Get arbitrary datetime
    """
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    return any_datetime_between(start, end)


def any_datetime_between(start: datetime, end: datetime) -> datetime:
    """
    Get arbitrary datetime between start (inclusive) and end (exclusive), with second precision.
    """
    range_in_seconds = (end - start).total_seconds()
    return start + timedelta(seconds=randint(0, int(range_in_seconds)))


def any_epoch_datetime_string() -> str:
    return format_rfc_3339_datetime_string(any_epoch_datetime())
