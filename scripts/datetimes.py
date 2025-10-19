from datetime import datetime, timezone

from dateutil import parser, tz

RFC_3339_DATE_FORMAT = "%Y-%m-%d"
RFC_3339_DATETIME_FORMAT = f"{RFC_3339_DATE_FORMAT}T%H:%M:%SZ"


def parse_rfc_3339_datetime(datetime_string: str) -> datetime:
    """Parse an RFC 3339 datetime string to a UTC datetime object.

    Args:
        datetime_string (str): RFC 3339 formatted datetime string.

    Returns:
        datetime: Timezone-aware UTC datetime object.

    >>> parse_rfc_3339_datetime("2001-02-03T04:05:06Z")
    datetime.datetime(2001, 2, 3, 4, 5, 6, tzinfo=datetime.timezone.utc)
    >>> original_datetime = datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    >>> parse_rfc_3339_datetime(format_rfc_3339_datetime_string(original_datetime)) == original_datetime
    True
    """
    naive_datetime = datetime.strptime(datetime_string, RFC_3339_DATETIME_FORMAT)
    return naive_datetime.replace(tzinfo=timezone.utc)


def parse_rfc_3339_date(date_string: str) -> datetime:
    """Parse an RFC 3339 date string to a UTC datetime object at midnight.

    Args:
        date_string (str): RFC 3339 formatted date string.

    Returns:
        datetime: Timezone-aware UTC datetime object at midnight.

    >>> parse_rfc_3339_date("2001-02-03")
    datetime.datetime(2001, 2, 3, 0, 0, tzinfo=datetime.timezone.utc)
    """
    return parse_rfc_3339_datetime(f"{date_string}T00:00:00Z")


def format_rfc_3339_datetime_string(datetime_object: datetime) -> str:
    """Format a timezone-aware datetime object as an RFC 3339 UTC string.

    Args:
        datetime_object (datetime): Timezone-aware datetime object.

    Returns:
        str: RFC 3339 formatted UTC datetime string.

    >>> datetime_object = datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    >>> format_rfc_3339_datetime_string(datetime_object)
    '2001-02-03T04:05:06Z'
    >>> datetime_object_nz = datetime(2001, 2, 3, 4, 5, 6, tzinfo=tz.gettz("Pacific/Auckland"))
    >>> format_rfc_3339_datetime_string(datetime_object_nz)
    '2001-02-02T15:05:06Z'
    >>> format_rfc_3339_datetime_string(datetime(2001, 2, 3, 4, 5, 6))
    Traceback (most recent call last):
    ...
    scripts.datetimes.NaiveDatetimeError: Can't convert naive datetime, timezone aware datetime object needed
    """
    if datetime_object.tzinfo is None:
        raise NaiveDatetimeError()

    return datetime_object.astimezone(timezone.utc).strftime(RFC_3339_DATETIME_FORMAT)


def format_rfc_3339_nz_midnight_datetime_string(datetime_object: datetime) -> str:
    """Convert datetime to New Zealand midnight and format it to UTC RFC 3339 string.

    Args:
        datetime_object (datetime): Timezone-aware datetime object.

    Returns:
        str: RFC 3339 formatted UTC datetime string for NZ midnight.

    >>> datetime_object = datetime(2001, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    >>> format_rfc_3339_nz_midnight_datetime_string(datetime_object)
    '2001-02-02T11:00:00Z'
    """
    naive_midnight_datetime_string = f"{datetime_object.strftime(RFC_3339_DATE_FORMAT)}T00:00:00.000"
    nz_tz = tz.gettz("Pacific/Auckland")
    try:
        nz_datetime = parser.parse(naive_midnight_datetime_string).replace(tzinfo=nz_tz)
    except parser.ParserError as err:
        raise Exception(f"Not a valid date: {err}") from err

    utc_tz = tz.gettz("UTC")
    datetime_utc = nz_datetime.astimezone(utc_tz)

    return format_rfc_3339_datetime_string(datetime_utc)


def convert_utc_to_nz(datetime_object: datetime) -> datetime:
    """Convert a UTC datetime to New Zealand time zone (Pacific/Auckland).

    Args:
        datetime_object (datetime): Timezone-aware UTC datetime object.

    Returns:
        datetime: Timezone-aware datetime object in Pacific/Auckland.

    >>> dt_utc = datetime(2001, 2, 2, 11, 0, 0, tzinfo=timezone.utc)
    >>> convert_utc_to_nz(dt_utc)
    datetime.datetime(2001, 2, 3, 0, 0, tzinfo=tzfile('...Pacific/Auckland'))
    >>> convert_utc_to_nz(datetime(2001, 2, 3, 4, 5, 6))
    Traceback (most recent call last):
    ...
    scripts.datetimes.NaiveDatetimeError: Can't convert naive datetime, timezone aware datetime object needed
    >>> dt_nz = datetime(2001, 2, 3, 4, 5, 6, tzinfo=tz.gettz("Pacific/Auckland"))
    >>> convert_utc_to_nz(dt_nz)
    Traceback (most recent call last):
    ...
    scripts.datetimes.NotUTCError: Input datetime must be in UTC
    """
    if datetime_object.tzinfo is None:
        raise NaiveDatetimeError()
    tzinfo = datetime_object.tzinfo
    if tzinfo != timezone.utc:
        raise NotUTCError()
    nz_tz = tz.gettz("Pacific/Auckland")
    return datetime_object.astimezone(nz_tz)


class NaiveDatetimeError(Exception):
    """Raised when attempting to format a naive datetime as RFC 3339 UTC."""

    def __init__(self) -> None:
        super().__init__("Can't convert naive datetime, timezone aware datetime object needed")


class NotUTCError(Exception):
    """Raised when input datetime is not in UTC for convert_utc_to_nz."""

    def __init__(self) -> None:
        super().__init__("Input datetime must be in UTC")
