import typing
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta, weekday


class RelativeDelta(relativedelta):
    """`dateutil.RelativeDelta.RelativeDelta` class with custom magic methods and constructor."""

    def __init__(
        self,
        years: int = 0,
        months: int = 0,
        days: int = 0,
        leapdays: int = 0,
        weeks: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        weekday: int | weekday | None = None,
        yearday: int | None = None,
        nlyearday: int | None = None,
        hour: int | None = None,
        minute: int | None = None,
        second: int | None = None,
        microsecond: int | None = None,
    ) -> None:
        super().__init__(
            dt1=None,
            dt2=None,
            years=years,
            months=months,
            days=days,
            leapdays=leapdays,
            weeks=weeks,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
            year=year,
            month=month,
            day=day,
            weekday=weekday,
            yearday=yearday,
            nlyearday=nlyearday,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
        )

        self._ts = datetime.fromtimestamp(timestamp=0, tz=pytz.utc)

    @property
    def s(self) -> int:
        """Returns rough estimate of total number of seconds in `RelativeDelta` object.

        ### WARNING: Only for rough estimations.

        This method is not safe to use with `RelativeDelta` objects that use
        `months` and `years` as a number of seconds in different months and years can vary.

        Despite that, the method tries to be as objective as possible and uses
        Unix Epoch as a measurement point to calculate the number of seconds.

        This method will always return the same result for objects with identical attributes.
        """
        return int((self._ts + self).timestamp())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s == other.s
        return super().__eq__(other)

    def __ne__(self, other: typing.Self) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s != other.s
        return super().__ne__(other)

    def __lt__(self, other: typing.Self) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s < other.s
        return super().__lt__(other)

    def __le__(self, other: typing.Self) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s <= other.s
        return super().__le__(other)

    def __gt__(self, other: typing.Self) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s > other.s
        return super().__gt__(other)

    def __ge__(self, other: typing.Self) -> bool:
        if isinstance(other, RelativeDelta):
            return self.s >= other.s
        return super().__ge__(other)
