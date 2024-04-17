from datetime import datetime, timezone

from dateutil import parser, tz

RFC_3339_DATE_FORMAT = "%Y-%m-%d"
RFC_3339_DATETIME_FORMAT = f"{RFC_3339_DATE_FORMAT}T%H:%M:%SZ"


class NotUtcDatetime(Exception):
    def __init__(self, time_zone_name: str | None):
        super().__init__(f"Not a UTC time zone: {time_zone_name}")


def format_rfc_3339_datetime_string(datetime_object: datetime) -> str:
    time_zone_name = datetime_object.tzname()
    if time_zone_name != "UTC":
        raise NotUtcDatetime(time_zone_name)

    return datetime_object.strftime(RFC_3339_DATETIME_FORMAT)


def format_rfc_3339_nz_midnight_datetime_string(datetime_object: datetime) -> str:
    """Convert datetime to New Zealand midnight and format it to UTC"""
    naive_midnight_datetime_string = f"{datetime_object.strftime(RFC_3339_DATE_FORMAT)}T00:00:00.000"

    nz_tz = tz.gettz("Pacific/Auckland")
    try:
        nz_datetime = parser.parse(naive_midnight_datetime_string).replace(tzinfo=nz_tz)
    except parser.ParserError as err:
        raise Exception(f"Not a valid date: {err}") from err

    utc_tz = tz.gettz("UTC")
    datetime_utc = nz_datetime.astimezone(utc_tz)

    return format_rfc_3339_datetime_string(datetime_utc)


def parse_rfc_3339_datetime(datetime_string: str) -> datetime:
    naive_datetime = datetime.strptime(datetime_string, RFC_3339_DATETIME_FORMAT)
    return naive_datetime.replace(tzinfo=timezone.utc)


def parse_rfc_3339_date(date_string: str) -> datetime:
    return parse_rfc_3339_datetime(f"{date_string}T00:00:00Z")
