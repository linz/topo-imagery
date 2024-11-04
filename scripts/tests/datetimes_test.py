from datetime import datetime, timedelta, timezone
from random import randint

from dateutil.tz import tz
from pytest import raises
from pytest_subtests import SubTests

from scripts.datetimes import (
    NaiveDatetimeError,
    format_rfc_3339_datetime_string,
    format_rfc_3339_nz_midnight_datetime_string,
    parse_rfc_3339_date,
    parse_rfc_3339_datetime,
)


def test_should_parse_rfc_3339_datetime() -> None:
    assert parse_rfc_3339_datetime("2001-02-03T04:05:06Z") == datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)


def test_should_parse_rfc_3339_date() -> None:
    assert parse_rfc_3339_date("2001-02-03") == datetime(2001, 2, 3, tzinfo=timezone.utc)


def test_should_format_utc_datetime_as_rfc_3339() -> None:
    datetime_object = datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    assert format_rfc_3339_datetime_string(datetime_object) == "2001-02-03T04:05:06Z"


def test_should_format_non_utc_datetime_as_rfc_3339() -> None:
    datetime_object = datetime(2001, 2, 3, 4, 5, 6, tzinfo=tz.gettz("Pacific/Auckland"))
    assert format_rfc_3339_datetime_string(datetime_object) == "2001-02-02T15:05:06Z"


def test_should_raise_error_when_formatting_a_naive_datetime(subtests: SubTests) -> None:
    for function in [format_rfc_3339_datetime_string, format_rfc_3339_nz_midnight_datetime_string]:
        with subtests.test(msg=function.__name__):
            with raises(NaiveDatetimeError, match="Can't convert naive datetime to UTC"):
                format_rfc_3339_datetime_string(datetime.now())


def test_should_be_able_to_invert_conversion() -> None:
    original_datetime = any_epoch_datetime()
    assert parse_rfc_3339_datetime(format_rfc_3339_datetime_string(original_datetime)) == original_datetime


def test_should_format_rfc_3339_nz_midnight_datetime_string() -> None:
    datetime_object = datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    assert format_rfc_3339_nz_midnight_datetime_string(datetime_object) == "2001-02-02T11:00:00Z"


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
