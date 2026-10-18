"""When email may go out: quiet hours and digest times, in the reader's own time zone.

Pure functions of a preference and a moment, so they are easy to test.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

DIGEST_HOUR = 8  # digests arrive at 08:00 local time; weekly ones on Mondays
WEEKLY_DAY = 0


def _local(preference, now: datetime) -> datetime:
    return now.astimezone(ZoneInfo(preference.timezone))


def _quiet(start: time, end: time, moment: time) -> bool:
    if start <= end:
        return start <= moment < end
    return moment >= start or moment < end  # spans midnight, e.g. 22:00–07:00


def quiet_until(preference, now: datetime) -> datetime | None:
    """The end of the current quiet period, or None when email may go out now."""
    start, end = preference.quiet_start, preference.quiet_end
    if start is None or end is None or start == end:
        return None
    local = _local(preference, now)
    if not _quiet(start, end, local.time()):
        return None
    ends = local.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    if ends <= local:
        ends += timedelta(days=1)
    return ends


def digest_due(preference, now: datetime) -> bool:
    if preference.digest == "off":
        return False
    local = _local(preference, now)
    if local.hour != DIGEST_HOUR or (
        preference.digest == "weekly" and local.weekday() != WEEKLY_DAY
    ):
        return False
    # The task runs hourly; this keeps a retried or doubled run from sending twice.
    return preference.last_digest_at is None or now - preference.last_digest_at > timedelta(
        hours=20
    )


def digest_window(preference, now: datetime) -> datetime:
    """Notifications newer than this go into the digest."""
    period = timedelta(days=7 if preference.digest == "weekly" else 1)
    return max(preference.last_digest_at or now - period, now - period)
