"""Time and date helpers"""

# Standard Library
import datetime
from pytz import timezone
import arrow
from arrow import Arrow
import typing as t

date_type = t.Union[datetime.datetime, datetime.time]


def now() -> datetime.datetime:
    """Get the current time as timezone-aware UTC timestamp.

    :return: Current datetime with UTC timezone
    """
    return datetime.datetime.now(datetime.timezone.utc)


def from_timestamp(unix_dt: float, tz: str) -> datetime.datetime:
    """Convert UNIX datetime to timestamp.

    :param tz: String representation of a timezone
    :param unix_dt: UNIX timestamps as float as seconds since 1970
    :return: Python datetime object
    """

    assert tz, "You need to give an explicit timezone when converting UNIX times to datetime objects"

    # From string to object
    tz = timezone(tz)
    ct = datetime.datetime.fromtimestamp(unix_dt, tz=tz)
    return ct


def arrow_format(dt: date_type, dt_format: str) -> str:
    """Format datetime using Arrow formatter string.

    Context must be a time/datetime object.

    :term:`Arrow` is a Python helper library for parsing and formatting datetimes.

    Example:

    .. code-block:: python
        dt = now()
        print(arrow_format(dt=dt, dt_format='YYYYMMDDHHMMss'))

    """
    assert isinstance(dt, (datetime.datetime, datetime.time)), "Got context {}".format(dt)
    a = arrow.get(dt)
    return a.format(fmt=dt_format)


def friendly_time(now: datetime.datetime, tz: t.Union[str, None]) -> str:
    """Format timestamp in human readable format.

    * Context must be a datetime object

    * Takes optional keyword argument timezone which is a timezone name as a string. Assume the source datetime is in
    this timezone.
    """
    if not now:
        return ""

    if tz:
        tz = timezone(tz)
    else:
        tz = datetime.timezone.utc

    # Make relative time between two timestamps
    now = now.astimezone(tz)
    arrow_ = Arrow.fromdatetime(now)
    other = Arrow.fromdatetime(datetime.datetime.utcnow())
    return arrow_.humanize(other)


def format_dt_tz(now: t.Optional[date_type] = None, **kw):
    """Format datetime in a certain timezone."""

    if not now:
        return ""

    tz = kw.get("timezone", None)
    if tz:
        tz = timezone(tz)
    else:
        tz = datetime.timezone.utc

    locale = kw.get("locale", "en_US")

    arrow = Arrow.fromdatetime(now, tzinfo=tz)

    # Convert to target timezone
    tz = kw.get("target_timezone")
    if tz:
        arrow = arrow.to(tz)
    else:
        tz = arrow.tzinfo

    format_ = kw.get("format", "YYYY-MM-DD HH:mm")

    text = arrow.format(format_, locale=locale)

    if kw.get("show_timezone"):
        text = text + " ({})".format(tz)

    return text
