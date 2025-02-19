import typing
from datetime import datetime

import numexpr
import pytz
from redis.asyncio import Redis as AsyncRedis

from app import schema
from app.config import config
from app.repository import Repository
from app.service.chat import ChatService
from app.service.entry import EntryService
from app.service.event import EventService
from app.service.occurrence import OccurrenceService
from app.util import RelativeDelta


class Service:
    def __init__(self, repository: Repository, redis: AsyncRedis) -> None:
        self._repository = repository

        self.chat = ChatService(repository=repository, redis=redis)
        self.event = EventService(repository=repository, redis=redis)
        self.occurrence = OccurrenceService(repository=repository, redis=redis)
        self.entry = EntryService(repository=repository)

    async def load_configuration(
        self,
        chat_id: int,
        configuration: schema.ConfigurationInput,
        configuration_raw: dict[str, typing.Any],
    ) -> None:
        from app import tasks

        await self.event.delete(filter_=schema.EventDeleteFilter(chat_id=chat_id))

        chat = schema.Chat(
            id=chat_id,
            timezone=configuration.timezone,
            config=configuration_raw,
        )

        await self.chat.upsert(chat=chat)

        for event_input in configuration.events:
            event = schema.Event(
                chat=chat,
                name=event_input.name,
                description=event_input.description,
                initial_date=event_input.initial_date,
                next_date=event_input.initial_date,
                periodicity=event_input.periodicity,
                offset=event_input.offset,
                times_occurred=event_input.times_occurred,
            )
            event = self.update_event_next_date(event=event)
            if event is None:
                continue

            tasks.send_notification_message_task.apply_async(
                kwargs={"event_id": event.id},
                eta=event.next_date - self.evaluate_event_offset(event=event),
            )

            await self.event.upsert(event=event)

    def update_event_next_date(self, event: schema.Event) -> schema.Event | None:
        """Update event's `next_date` to be the closest possible occurrence date.

        Returns `None` if an event will never occur again,
        which is when `periodicity` is `None` and `next_date` already passed
        or `periodicity` end up being outside of the allowed range.

        Else `schema.Event` object is returned.
        """
        ts = datetime.now(tz=pytz.utc) + RelativeDelta(seconds=30)

        while event.next_date <= ts + self.evaluate_event_offset(event=event):
            if not (periodicity := self.evaluate_event_periodicity(event=event)):
                return None

            event.next_date += periodicity
            event.times_occurred += 1

        return event

    def evaluate_event_periodicity(self, event: schema.Event) -> RelativeDelta | None:
        """Evaluate `util.RelativeDelta` object for next event occurrance.

        If event has no periodicity rules specified
        or if event periodicity is not within the allowed range, None is returned.

        Returns `util.RelativeDelta` object.
        """
        if not event.periodicity:
            return None

        periodicity = self.evaluate_period(period=event.periodicity, t=event.times_occurred)
        if not (config.min_periodicity <= periodicity <= config.max_periodicity):
            return None

        return periodicity

    def evaluate_event_offset(self, event: schema.Event) -> RelativeDelta:
        """Evaluate offset for `next_date`.

        If event has no offset rules specified
        or if event offset is not within the allowd range, empty offset returned (0 seconds).

        Returns `util.RelativeDelta` object.
        """
        if not event.offset:
            return RelativeDelta()

        offset = self.evaluate_period(period=event.offset, t=event.times_occurred)
        if not (config.min_offset <= offset <= config.max_offset):
            return RelativeDelta()

        return offset

    @staticmethod
    def evaluate_period(period: schema.Period, t: int) -> RelativeDelta:
        """Evaluate `schema.Period` object with `t` and `n` variables. Where `n = t + 1`.

        Returns `util.RelativeDelta` object.
        """

        def evaluate(ex: str | None) -> int:
            if ex is None:
                return 0
            return round(numexpr.evaluate(ex, {"t": t, "n": t + 1}, {}).item())

        return RelativeDelta(**{key: evaluate(value) for key, value in period.model_dump().items()})
